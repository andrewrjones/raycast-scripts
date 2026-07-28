#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy Current Page URL as Markdown
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
	-- Test seam: `./current-page-as-markdown.applescript --clean-title "(1) A page"` cleans a
	-- title without touching a browser or the clipboard.
	if (count of argv) is 2 and item 1 of argv is "--clean-title" then
		return cleanedTitle(item 2 of argv)
	end if

	set browserName to frontmostBrowser()
	if browserName is "" then return "Not a supported browser"

	set thePage to frontPage(browserName)
	set theURL to pageURL of thePage
	set linkText to cleanedTitle(pageTitle of thePage)
	if linkText is "" then set linkText to theURL

	set theLink to "[" & linkText & "](" & markdownURL(theURL) & ")"
	set the clipboard to theLink
	return theLink
end run

on frontmostBrowser()
	tell application "System Events"
		set appName to name of first process whose frontmost is true
	end tell
	if appName is "Safari" or appName is "Google Chrome" then return appName
	return ""
end frontmostBrowser

on frontPage(browserName)
	if browserName is "Safari" then
		tell application "Safari"
			if (count of windows) is 0 then error "No Safari window is open"
			set activeTab to current tab of front window
			set foundURL to URL of activeTab
			-- A tab's name is the page's own title. A document's or window's name is prefixed
			-- with the Safari profile name ("Personal — Some page"), which has no place in
			-- the link, so neither is used here.
			set foundTitle to name of activeTab
			if foundTitle is "" then
				-- Needs Develop > Allow JavaScript from Apple Events.
				try
					set jsTitle to (do JavaScript "document.title" in activeTab)
					if jsTitle is not missing value then set foundTitle to jsTitle as text
				end try
			end if
		end tell
	else
		tell application "Google Chrome"
			if (count of windows) is 0 then error "No Chrome window is open"
			set activeTab to active tab of front window
			set foundURL to URL of activeTab
			set foundTitle to title of activeTab
		end tell
	end if
	return {pageTitle:foundTitle, pageURL:foundURL}
end frontPage

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
