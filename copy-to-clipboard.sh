#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy to clipboard
# @raycast.mode silent
# @raycast.refreshTime 1h

# Optional parameters:
# @raycast.icon 📋
# @raycast.needsConfirmation false
# @raycast.argument1 { "type": "text", "placeholder": "input text", "percentEncoded": true }

# Documentation:
# @raycast.author andrewjones
# @raycast.authorURL https://andrew-jones.com

if [ -z "$1" ]; then
  echo "Please provide an input to copy."
  exit 1
fi

echo "$1" | pbcopy

echo "Copied to clipboard: $1"
