import config
import json

files = [
  "./languages/en.json",
]

DEFAULT = "en"

translations = {}
for file in files:
  with open(file, "r") as file:
    values = json.load(file)
    translations[values["code"]] = values

class LanguageService:
  @staticmethod
  def get_default_code():
    return DEFAULT

  @staticmethod
  def get_all_codes() -> list[str]:
    return list(translations.keys())
  
  @staticmethod
  def get_next_code(prev: str) -> str:
    codes = LanguageService.get_all_codes()
    try:    
      i = codes.index(prev)
      new_i = i + 1
      if new_i >= len(codes):
        return codes[0]
      return codes[new_i]
    except ValueError:
      return LanguageService.get_default_code()
    
  @staticmethod
  def get_translation(code: str, quote: str) -> str:
    return translations[code][quote]