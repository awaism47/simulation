import re

def remove_numbers_from_string(s):
    # Replace all occurrences of digits with an empty string
    string_without_numbers = re.sub(r'\d+', '', s)

    # Optionally, you might want to strip leading/trailing whitespace
    string_without_numbers = string_without_numbers.strip()

    return string_without_numbers
