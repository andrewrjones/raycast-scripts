#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Number to English
# @raycast.mode compact
# @raycast.refreshTime 1h

# Optional parameters:
# @raycast.icon 🔢
# @raycast.needsConfirmation false
# @raycast.argument1 { "type": "text", "placeholder": "input number", "percentEncoded": true }

# Documentation:
# @raycast.author andrewjones
# @raycast.authorURL https://andrew-jones.com

import sys

def number_to_words(num):
    """Convert a number to its English word representation."""
    
    # Handle special case
    if num == 0:
        return "Zero"
    
    # Define word mappings
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", 
            "seventeen", "eighteen", "nineteen"]
    
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    thousands = ["", "thousand", "million", "billion", "trillion"]
    
    def convert_hundreds(n):
        """Convert a number less than 1000 to words."""
        result = ""
        
        if n >= 100:
            result += ones[n // 100] + " hundred"
            n %= 100
            if n > 0:
                result += " and "
        
        if n >= 20:
            result += tens[n // 10]
            if n % 10 > 0:
                result += "-" + ones[n % 10]
        elif n > 0:
            result += ones[n]
        
        return result
    
    # Handle negative numbers
    if num < 0:
        return "negative " + number_to_words(-num)
    
    # Split number into groups of three digits
    groups = []
    while num > 0:
        groups.append(num % 1000)
        num //= 1000
    
    # Convert each group to words
    result_parts = []
    for i, group in enumerate(reversed(groups)):
        if group > 0:
            group_words = convert_hundreds(group)
            if i < len(thousands) - 1:
                group_words += " " + thousands[len(groups) - 1 - i]
            result_parts.append(group_words)
    
    result = " ".join(result_parts)
    
    # Capitalize first letter
    return result.capitalize()

# Get text from command line argument
if len(sys.argv) < 2:
    print("Please provide a number as a command line argument.")
    sys.exit(1)

number_input = sys.argv[1]

try:
    # Remove any commas and convert to integer
    number = int(number_input.replace(",", ""))
    result = number_to_words(number)
    print(result)
except ValueError:
    print(f"Error: '{number_input}' is not a valid number.")
    sys.exit(1)

