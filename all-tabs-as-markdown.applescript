#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy All Tabs as Markdown List
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🔗

# Documentation:
# @raycast.author andrewjones
# @raycast.authorURL https://andrew-jones.com

use AppleScript version "2.4" -- Yosemite (10.10) or later
use framework "Foundation"
use scripting additions

property NSString : a reference to current application's NSString
property NSCharacterSet : a reference to current application's NSCharacterSet
property NSRegularExpressionSearch : 1024

on run argv
	-- Test seam: `./all-tabs-as-markdown.applescript --clean-title "(1) A page"` cleans a
	-- title without touching a browser or the clipboard.
	if (count of argv) is 2 and item 1 of argv is "--clean-title" then
		return cleanedTitle(item 2 of argv)
	end if

	set browserName to frontmostBrowser()
	if browserName is "" then return "Not a supported browser"

	set thePages to windowPages(browserName)
	if thePages is {} then return "No tabs are open"

	set theLines to {}
	repeat with thePage in thePages
		set theURL to pageURL of thePage
		set linkText to cleanedTitle(pageTitle of thePage)
		if linkText is "" then set linkText to theURL
		set end of theLines to "- [" & linkText & "](" & markdownURL(theURL) & ")"
	end repeat

	set theList to joinLines(theLines)
	set the clipboard to theList
	return theList
end run

on frontmostBrowser()
	tell application "System Events"
		set appName to name of first process whose frontmost is true
	end tell
	if appName is "Safari" or appName is "Google Chrome" then return appName
	return ""
end frontmostBrowser

on windowPages(browserName)
	set thePages to {}
	if browserName is "Safari" then
		tell application "Safari"
			if (count of windows) is 0 then error "No Safari window is open"
			repeat with aTab in tabs of front window
				-- A tab's name is the page's own title (no profile prefix); fall back to the URL.
				set foundTitle to name of aTab
				set end of thePages to {pageTitle:foundTitle, pageURL:(URL of aTab)}
			end repeat
		end tell
	else
		tell application "Google Chrome"
			if (count of windows) is 0 then error "No Chrome window is open"
			repeat with aTab in tabs of front window
				set end of thePages to {pageTitle:(title of aTab), pageURL:(URL of aTab)}
			end repeat
		end tell
	end if
	return thePages
end windowPages

on joinLines(theLines)
	set {oldDelims, AppleScript's text item delimiters} to {AppleScript's text item delimiters, linefeed}
	set joined to theLines as text
	set AppleScript's text item delimiters to oldDelims
	return joined
end joinLines

on cleanedTitle(rawTitle)
	set theTitle to rawTitle as text
	-- Sites such as Notion prefix the title with an unread count, either at the front or just
	-- after the page's emoji: "(3) A page", "🤔 (3) A page". Anchored, and only non-word
	-- characters may precede the count, so parenthesised digits elsewhere in a title survive.
	set theTitle to regexReplace(theTitle, "^(\\W*?)\\(\\d+\\)\\s*", "$1")
	set theTitle to regexReplace(theTitle, "\\s+", " ")
	-- Escape the characters that would otherwise close the Markdown link text early.
	set theTitle to regexReplace(theTitle, "([\\[\\]])", "\\\\$1")
	return trimmed(theTitle)
end cleanedTitle

on markdownURL(theURL)
	-- Parentheses or spaces would break a bare URL; the angle-bracket form is unambiguous.
	if theURL contains "(" or theURL contains ")" or theURL contains " " then
		return "<" & theURL & ">"
	end if
	return theURL
end markdownURL

on regexReplace(theText, thePattern, theTemplate)
	set subject to NSString's stringWithString:theText
	set replaced to subject's stringByReplacingOccurrencesOfString:thePattern withString:theTemplate options:NSRegularExpressionSearch range:{0, subject's |length|()}
	return replaced as text
end regexReplace

on trimmed(theText)
	set subject to NSString's stringWithString:theText
	set whitespace to NSCharacterSet's whitespaceAndNewlineCharacterSet()
	return (subject's stringByTrimmingCharactersInSet:whitespace) as text
end trimmed
