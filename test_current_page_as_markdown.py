"""End-to-end tests for current-page-as-markdown.applescript.

Run with:  uv run --with pytest pytest test_current_page_as_markdown.py -v

These tests drive a real browser, because the defects they cover only appear there.
Fixture pages are served over localhost (Safari blocks file:// access from Apple Events)
and carry deliberately awkward titles. Page names are invented, not real pages.

The terminal running these tests needs Automation permission for Safari, Google Chrome and
System Events (System Settings > Privacy & Security > Automation).

The tests take over the front browser window and steal focus while they run.
The clipboard is saved and restored around the suite.
"""

import functools
import html
import http.server
import subprocess
import threading
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "current-page-as-markdown.applescript"

BROWSERS = {
    "Safari": "/Applications/Safari.app",
    "Google Chrome": "/Applications/Google Chrome.app",
}

# (page title, expected Markdown link text)
PAGE_TITLE_CASES = [
    # Notion and friends prefix the title with an unread count.
    ("(1) Widget rollout postponed until Q3", "Widget rollout postponed until Q3"),
    # ...but parentheses that are part of the title must survive.
    ("Widget rollout (postponed)", "Widget rollout (postponed)"),
    ("(draft) widget rollout", "(draft) widget rollout"),
    # Characters that an HTML round-trip would eat.
    ("Widget <beta> rollout", "Widget <beta> rollout"),
    ("Tea & biscuits inventory", "Tea & biscuits inventory"),
    # Brackets would otherwise terminate the Markdown link text.
    ("Widget [draft] rollout", r"Widget \[draft\] rollout"),
    ("Widget rollout — phase 2 🚀", "Widget rollout — phase 2 🚀"),
    # Notion's real shape: the unread count follows the page's emoji.
    ("🤔 (5) Widget rollout | Notion", "🤔 Widget rollout | Notion"),
]

# Cleaning that the browser itself normalises away, so it is exercised directly instead.
CLEAN_TITLE_CASES = [
    ("(1) Widget rollout", "Widget rollout"),
    ("  Widget   rollout  ", "Widget rollout"),
    ("Widget\nrollout", "Widget rollout"),
    # An unread count counts as leading when only the page's emoji precedes it.
    ("🤔 (5) Widget rollout | Notion", "🤔 Widget rollout | Notion"),
    # Anywhere else, parenthesised digits are part of the title.
    ("Widget (1) rollout", "Widget (1) rollout"),
    ("🚀 Widget (1) rollout", "🚀 Widget (1) rollout"),
    ("(one) Widget rollout", "(one) Widget rollout"),
    # A separator that looks like Safari's profile prefix is not one, and is left alone.
    ("Andrew - my blog", "Andrew - my blog"),
    ("Widget rollout — phase 2", "Widget rollout — phase 2"),
]


def osascript(source: str) -> str:
    """Run AppleScript source, returning its result."""
    done = subprocess.run(
        ["osascript", "-"], input=source, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def run_script(*args: str) -> str:
    """Run the script under test the way Raycast does, returning its stdout."""
    done = subprocess.run(
        [str(SCRIPT), *args], capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


@pytest.fixture(scope="session")
def fixture_pages(tmp_path_factory):
    """Serve one page per title case over localhost; yields title -> URL."""
    directory = tmp_path_factory.mktemp("pages")
    urls_by_title = {}
    for index, (title, _) in enumerate(PAGE_TITLE_CASES):
        page = directory / f"page{index}.html"
        page.write_text(
            "<!doctype html>"
            f"<html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head>"
            "<body>fixture</body></html>",
            encoding="utf-8",
        )
        urls_by_title[title] = page.name

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    handler.log_message = lambda *args, **kwargs: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    base = f"http://127.0.0.1:{server.server_address[1]}/"
    try:
        yield base, {title: base + name for title, name in urls_by_title.items()}
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="session", autouse=True)
def preserved_clipboard():
    """Leave the user's clipboard as we found it."""
    before = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout
    yield
    subprocess.run(["pbcopy"], input=before, text=True)


@pytest.fixture(params=list(BROWSERS))
def browser(request, fixture_pages):
    """A browser with one dedicated tab, closed again afterwards."""
    name = request.param
    if not Path(BROWSERS[name]).exists():
        pytest.skip(f"{name} is not installed")
    base, _ = fixture_pages
    yield name
    close_fixture_tabs(name, base)


def open_page(browser: str, url: str, base: str) -> None:
    """Point the browser's dedicated fixture tab at url, creating it if needed."""
    if browser == "Safari":
        osascript(f'''
            tell application "Safari"
                activate
                if (count of documents) is 0 then make new document
                set reused to false
                repeat with candidate in tabs of window 1
                    if (URL of candidate as text) starts with "{base}" then
                        set URL of candidate to "{url}"
                        set current tab of window 1 to candidate
                        set reused to true
                        exit repeat
                    end if
                end repeat
                if not reused then
                    tell window 1
                        set current tab to (make new tab with properties {{URL:"{url}"}})
                    end tell
                end if
            end tell
        ''')
    else:
        osascript(f'''
            tell application "Google Chrome"
                activate
                if (count of windows) is 0 then make new window
                set reused to false
                repeat with candidate in tabs of window 1
                    if (URL of candidate as text) starts with "{base}" then
                        set URL of candidate to "{url}"
                        set active tab index of window 1 to index of candidate
                        set reused to true
                        exit repeat
                    end if
                end repeat
                if not reused then
                    tell window 1 to make new tab with properties {{URL:"{url}"}}
                end if
            end tell
        ''')


def close_fixture_tabs(browser: str, base: str) -> None:
    """Close every fixture tab, one per pass since closing one shifts the tab indices."""
    application = "Safari" if browser == "Safari" else "Google Chrome"
    osascript(f'''
        on firstFixtureTab()
            tell application "{application}"
                repeat with aWindow in windows
                    repeat with candidate in (tabs of aWindow)
                        if (URL of candidate as text) starts with "{base}" then return candidate
                    end repeat
                end repeat
            end tell
            return missing value
        end firstFixtureTab

        repeat
            set target to firstFixtureTab()
            if target is missing value then exit repeat
            tell application "{application}" to close target
        end repeat
    ''')


def reported_title(browser: str) -> str:
    """A readiness signal only: Safari's document name still carries the profile prefix,
    so callers match on containment rather than equality."""
    if browser == "Safari":
        return osascript('tell application "Safari" to return name of document 1')
    return osascript(
        'tell application "Google Chrome" to return title of active tab of front window'
    )


def wait_for_frontmost(application: str, timeout: float = 15.0) -> None:
    """Block until the application is frontmost, which is how the script picks its source."""
    deadline = time.monotonic() + timeout
    last_seen = ""
    while time.monotonic() < deadline:
        last_seen = osascript(
            'tell application "System Events"'
            " to return name of first process whose frontmost is true"
        )
        if last_seen == application:
            return
        osascript(f'tell application "{application}" to activate')
        time.sleep(0.3)
    raise AssertionError(f"{application} never became frontmost; saw {last_seen!r}")


def wait_for_page(browser: str, title: str, timeout: float = 15.0) -> None:
    """Block until the browser is frontmost and reporting the loaded page's title."""
    deadline = time.monotonic() + timeout
    last_seen = ""
    while time.monotonic() < deadline:
        last_seen = reported_title(browser)
        if title in last_seen:
            wait_for_frontmost(browser)
            return
        time.sleep(0.2)
    raise AssertionError(f"{browser} never reported title {title!r}; saw {last_seen!r}")


@pytest.mark.parametrize("title,expected_text", PAGE_TITLE_CASES)
def test_copies_page_as_markdown_link(browser, fixture_pages, title, expected_text):
    base, urls = fixture_pages
    url = urls[title]
    open_page(browser, url, base)
    wait_for_page(browser, title)

    link = run_script()

    assert link == f"[{expected_text}]({url})"
    assert subprocess.run(["pbpaste"], capture_output=True, text=True).stdout == link


@pytest.mark.parametrize("raw,expected", CLEAN_TITLE_CASES)
def test_cleans_title(raw, expected):
    assert run_script("--clean-title", raw) == expected


def test_safari_title_excludes_profile_prefix(fixture_pages):
    """Safari prefixes a document's name with its profile name; the link must not show it."""
    if not Path(BROWSERS["Safari"]).exists():
        pytest.skip("Safari is not installed")
    base, urls = fixture_pages
    title, expected_text = PAGE_TITLE_CASES[1]
    open_page("Safari", urls[title], base)
    wait_for_page("Safari", title)
    try:
        document_name = osascript('tell application "Safari" to return name of document 1')
        if document_name == title:
            pytest.skip("this Safari window is not using a profile, so there is no prefix")
        assert document_name.endswith(title), (
            f"expected a profile prefix on {document_name!r}"
        )

        assert run_script() == f"[{expected_text}]({urls[title]})"
    finally:
        close_fixture_tabs("Safari", base)


def test_reports_unsupported_application():
    osascript('tell application "Finder" to activate')
    wait_for_frontmost("Finder")

    assert run_script() == "Not a supported browser"


def test_markdown_is_plain_text(browser, fixture_pages):
    """The Markdown must land on the clipboard as text, not as styled rich text."""
    base, urls = fixture_pages
    title, _ = PAGE_TITLE_CASES[0]
    open_page(browser, urls[title], base)
    wait_for_page(browser, title)

    run_script()

    types = subprocess.run(
        ["osascript", "-e", "return (clipboard info) as text"],
        capture_output=True,
        text=True,
    ).stdout
    assert "RTF" not in types
