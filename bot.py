import logging

import config
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.exceptions import TelegramForbiddenError
from ngrok_executor import get_webhook_host
from services.user import UserService
from aiogram.types import FSInputFile
from aiohttp import web
from db import db
import os

CACHE_FOLDER = "cache"

bot = Bot(config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def on_startup(bot: Bot):
    webhook_host = await get_webhook_host(config.NGROK_HOST)
    webhook_url = f"{webhook_host}{config.WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    await db.create_db_and_tables()
    for admin in config.ADMIN_ID_LIST:
        try:
            await bot.send_message(admin, 'Bot is working')
        except Exception as e:
            logging.warning(e)

async def on_shutdown():
    logging.warning('Shutting down..')

    await bot.delete_webhook()
    await dp.storage.close()
    

    logging.warning('Bye!')

async def buy_notification_handler(request: web.Request):
    data = await request.json()
    recipient = data.get("recipient")
    gift_id = data.get("id")
    gift_price = data.get("price")
    gift_title = data.get("title")
    gift_supply = data.get("supply")
    gift_file_id = data.get("file_id")
    amount_succeeded = data.get("amount_succeeded")
    amount_tried = data.get("amount_tried")
    error = data.get("error")
    if not all([recipient, gift_id, gift_file_id]):
      return web.json_response({"status": "error"}, status=web.HTTPBadRequest.status_code)
    
    try:
      recipient = int(recipient)
    except ValueError:
      return web.json_response({"status": "error", "error": "invalid user"}, status=web.HTTPForbidden.status_code)
       
    user = await UserService.get_by_tgid(recipient)
    if user is None:
      return web.json_response({"status": "error", "error": "invalid user"}, status=web.HTTPForbidden.status_code)

    if not user.can_receive_messages:
      return web.json_response({"status": "error", "error": "user unreachable"}, status=web.HTTPForbidden.status_code)
    
    t = f" \"{gift_title}\"" if gift_title is not None else ""
    message_text = (
      f"<b>Completed</b>: sent <b>{amount_succeeded}</b> of <b>{amount_tried}</b>{t} gifts\n"
      f"<b>Actual cost</b>: <b>{gift_price * amount_succeeded}</b> ⭐\n\n"
      f"<span class=\"tg-spoiler\">"
      f"ID: {gift_id}\n"
      f"TITLE: {gift_title or 'untitled'}\n"
      f"PRICE: {gift_price} stars\n"
      f"SUPPLY: {gift_supply or 'unlimited'}\n"
      f"ERROR: {error}"
      f"</span>")
    try:
      os.makedirs(CACHE_FOLDER, exist_ok=True)
      filepath = os.path.join(CACHE_FOLDER, f"{gift_id}.tgs")

      if not os.path.exists(filepath):
        file_obj = await bot.get_file(gift_file_id)
        await bot.download_file(file_obj.file_path, destination=filepath)

      sticker = FSInputFile(filepath)
      msg = await bot.send_sticker(recipient, sticker)

      await bot.send_message(recipient, message_text, reply_to_message_id=msg.message_id)
    except TelegramForbiddenError as e:
      await UserService.update_receive_messages(recipient, False)
      return web.json_response({"status": "error", "error": "user unreachable"}, status=web.HTTPForbidden.status_code)

    return web.json_response({"status": "ok"})

def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    app.router.add_post("/buy_notification", buy_notification_handler)
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=config.WEBAPP_HOST, port=int(config.WEBAPP_PORT))
