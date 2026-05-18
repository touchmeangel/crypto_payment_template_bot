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
import os

CACHE_FOLDER = "cache"

bot = Bot(config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def on_startup(bot: Bot):
    webhook_host = await get_webhook_host(config.NGROK_HOST)
    webhook_url = f"{webhook_host}{config.WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
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

def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=config.WEBAPP_HOST, port=int(config.WEBAPP_PORT))
