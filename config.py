from dotenv import load_dotenv
import json
import os

load_dotenv()

NGROK_HOST = os.environ.get("NGROK_HOST")
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH")
WEBAPP_HOST = os.environ.get("WEBAPP_HOST")
WEBAPP_PORT = os.environ.get("WEBAPP_PORT")
TOKEN = os.environ.get("TOKEN")
BSC_RPC = os.getenv("BSC_RPC")
BASE_RPC = os.getenv("BASE_RPC")
FAQ_LINK = os.environ.get("FAQ_LINK")
SUPPORT_LINK = os.environ.get("SUPPORT_LINK")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK")
CHANNEL_NAME = os.environ.get("CHANNEL_NAME")
ADMIN_ID_LIST = json.loads(os.environ.get("ADMIN_ID_LIST"))