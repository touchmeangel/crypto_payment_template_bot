from aiogram import types, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.common.common import get_back_to_menu_button, send_message
from handlers.user.payment_test import create_payment_test_callback
from utils.custom_filters import AdminIdFilter
import aiogram.types as types
import aiogram.enums as enums
from typing import Union
from bot import bot

start_router = Router()

class StartCallback(CallbackData, prefix="main"):
  level: int

def create_callback_start(level: int) -> str:
  return StartCallback(level=level).pack()

@start_router.message(Command(commands=["start"]))
async def start(message: Union[types.Message, types.CallbackQuery]):
  await send_message(message, "Please support this <a href=\"https://github.com/touchmeangel/crypto_payment_template_bot\">repo</a> with a star 🥺", reply_markup=main_markup())

def main_markup():
  test_button = types.InlineKeyboardButton(text="PAYMENT TEST", callback_data=create_payment_test_callback(0))

  return types.InlineKeyboardMarkup(inline_keyboard=[[test_button]])

@start_router.callback_query(StartCallback.filter())
async def start_menu_navigation(callback: types.CallbackQuery, callback_data: StartCallback):
  current_level = callback_data.level

  levels = {
    0: start,
  }

  current_level_function = levels[current_level]
  await current_level_function(callback)