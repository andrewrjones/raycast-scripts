#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy Current Page URL as Rich text
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🔗

# Documentation:
# @raycast.author andrewjones
# @raycast.authorURL https://andrew-jones.com

-- source: https://forum.latenightsw.com/t/html-styled-text-in-a-variable/2285/4

use AppleScript version "2.4" -- Yosemite (10.10) or later
use framework "Foundation"
use framework "AppKit"
use scripting additions

-- classes, constants, and enums used
property NSUTF8StringEncoding : a reference to 4
property NSString : a reference to current application's NSString
property NSAttributedString : a reference to current application's NSAttributedString

-- get the URL and page title as a HTML link
property theLink : ""
tell application "System Events"
    set frontmostProcess to first process where it is frontmost
    set appName to name of frontmostProcess
end tell
tell application appName
    set windowName to the name of the front window
end tell
if appName is equal to "Safari" then
    tell application "Safari"
		-- A tab's name is the page's own title. A document's or window's name is prefixed with
		-- the Safari profile name ("Personal — Some page"), which has no place in the link.
		set activeTab to current tab of front window
		set theLink to "<a href='" & URL of activeTab & "'>" & name of activeTab & "</a>"
    end tell
else if appName is equal to "Google Chrome" then
    tell application "Google Chrome"
		set activeTab to active tab of front window
		set theLink to "<a href='" & URL of activeTab & "'>" & title of activeTab & "</a>"
	end tell
end if

-- convert to data
set htmlString to NSString's stringWithString:theLink
set htmlData to htmlString's dataUsingEncoding:NSUTF8StringEncoding
-- make attributed string
set attString to NSAttributedString's alloc()'s initWithHTML:htmlData documentAttributes:(missing value)
-- get pasteboard
set pb to current application's NSPasteboard's generalPasteboard()
pb's clearContents()
pb's writeObjects:{attString}

return theLink
