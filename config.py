from dotenv import load_dotenv
import random
import json
import os

load_dotenv()

NGROK_HOST = os.environ.get("NGROK_HOST")
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH")
WEBAPP_HOST = os.environ.get("WEBAPP_HOST")
WEBAPP_PORT = os.environ.get("WEBAPP_PORT")
TOKEN = os.environ.get("TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
BSC_RPC = os.getenv("BSC_RPC")
BASE_RPC = os.getenv("BASE_RPC")
FAQ_LINK = os.environ.get("FAQ_LINK")
SUPPORT_LINK = os.environ.get("SUPPORT_LINK")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK")
CHANNEL_NAME = os.environ.get("CHANNEL_NAME")
PRICE_30_DAYS = float(os.environ.get("PRICE_30_DAYS"))
ADMIN_ID_LIST = json.loads(os.environ.get("ADMIN_ID_LIST"))
REQUIRED_CHANNEL_IDS = json.loads(os.environ.get("REQUIRED_CHANNEL_IDS"))
REQUIRED_CHANNEL_LINKS = json.loads(os.environ.get("REQUIRED_CHANNEL_LINKS"))
REQUIRED_CHANNEL_NAMES = json.loads(os.environ.get("REQUIRED_CHANNEL_NAMES"))
if len(REQUIRED_CHANNEL_IDS) != len(REQUIRED_CHANNEL_LINKS) or len(REQUIRED_CHANNEL_LINKS) != len(REQUIRED_CHANNEL_NAMES):
  raise RuntimeError("invalid required channels")

config_file = "config.json"
if not os.path.exists(config_file):
  raise RuntimeError(f"{config_file} file is required.")

with open(config_file) as f:
  config = json.load(f)

proxies = config["proxies"]
creds = config["api_credentials"]
if len(creds) <= 0:
  raise RuntimeError("at least 1 pair of api_id and api_hash is required.")

def random_creds() -> tuple[int, str]:
  choice = random.choice(creds)
  return choice["api_id"], choice["api_hash"]

def random_proxy() -> str | None:
  if len(proxies) <= 0:
    return None
  
  return random.choice(proxies)