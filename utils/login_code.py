import re

def validate_login_code(login_code: str):
  digits_only = re.sub(r"[^\d]+", "", login_code)
  return digits_only