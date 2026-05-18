import re

def is_valid_phone_number(phone_number: str) -> bool:
    pattern = r"^\+?[1-9][0-9]{7,14}$"
    return bool(re.match(pattern, phone_number))