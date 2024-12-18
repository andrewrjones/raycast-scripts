#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Readtime
# @raycast.mode silent
# @raycast.refreshTime 1h

# Optional parameters:
# @raycast.icon 🕐
# @raycast.needsConfirmation false
# @raycast.argument1 { "type": "text", "placeholder": "input text", "percentEncoded": true }

# Documentation:
# @raycast.author andrewjones
# @raycast.authorURL https://andrew-jones.com

import sys
import math
import re

# Constants
WPM = 265

# Get text from command line argument
if len(sys.argv) < 2:
    print("Please provide text as a command line argument.")
    sys.exit(1)

text = sys.argv[1]

# Split text into words using regex to match non-word characters
words = len(re.findall(r'\w+', text))

# Calculate reading time in minutes
mins = math.ceil(words / WPM)

# Print the estimated reading time
print(str(mins) + " minutes")

