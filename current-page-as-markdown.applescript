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

-- source: https://forum.latenightsw.com/t/html-styled-text-in-a-variable/2285/4

use AppleScript version "2.4" -- Yosemite (10.10) or later
use framework "Foundation"
use framework "AppKit"
use scripting additions

-- classes, constants, and enums used
property NSUTF8StringEncoding : a reference to 4
property NSString : a reference to current application's NSString
property NSAttributedString : a reference to current application's NSAttributedString

on cleanTitle(inputString)
    -- Check if the input string contains the pattern "(number) title"
    if inputString contains "(" then
        -- Remove the leading number and whitespace
        set titlePart to text ((offset of ")" in titlePart) + 2) through -1 of titlePart
        return titlePart
    else
        -- If the input is already just a title, return it as is
        return inputString
    end if
end cleanTitle

property theLink : ""

tell application "System Events"
    set frontmostProcess to first process where it is frontmost
    set appName to name of frontmostProcess
end tell
tell application appName
    set windowName to the name of the front window
end tell
if appName is equal to "Safari" then
    tell application "Safari" to tell document 1
        set cleanTitle to my cleanTitle(name)
		set theLink to "[" & cleanTitle & "](" & URL & ")"
    end tell
else if appName is equal to "Google Chrome" then
	tell application "Google Chrome"
		set activeTab to active tab of front window
        set cleanTitle to my cleanTitle(title of activeTab)
		set theLink to "[" & cleanTitle & "](" & URL of activeTab & ")"
	end tell
else
    set theLink to ""
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
