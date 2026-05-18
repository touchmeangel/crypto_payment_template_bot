from aiogram import types, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.common.common import get_back_to_menu_button, send_message
from handlers.user.my_profile import create_callback_profile
from handlers.user.accounts import create_callback_accounts
from handlers.user.autobuy import create_callback_autobuy
from utils.custom_filters import AdminIdFilter
import aiogram.types as types
import aiogram.enums as enums
from typing import Union
from bot import bot

from config import CHANNEL_LINK, CHANNEL_NAME, SUPPORT_LINK, FAQ_LINK, REQUIRED_CHANNEL_IDS, REQUIRED_CHANNEL_LINKS, REQUIRED_CHANNEL_NAMES
from language import LanguageService
from services.user import UserService

start_router = Router()

class StartCallback(CallbackData, prefix="main"):
    level: int

def create_callback_start(level: int) -> str:
    return StartCallback(level=level).pack()

@start_router.message(Command(commands=["start"]))
async def start(message: Union[types.Message, types.CallbackQuery]):
  user_telegram_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
  user_telegram_username = message.from_user.username
  await UserService.user_logged(user_telegram_id, user_telegram_username)
  await check_subs(message)

async def check_subs(message: Union[types.Message, types.CallbackQuery]):
  user_telegram_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
  language_code = await UserService.get_language_code(user_telegram_id)

  chats_to_join = []
  for chat_i, chat_id in enumerate(REQUIRED_CHANNEL_IDS):     
    member = await bot.get_chat_member(chat_id, user_telegram_id)
    if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.CREATOR, enums.ChatMemberStatus.MEMBER]:
      chats_to_join.append(chat_i)
  
  if len(chats_to_join) > 0:
    join = LanguageService.get_translation(language_code, "join")
    msg = (f"{join}\n\n")
    for chat_i in chats_to_join:
      msg += f"<a href=\"{REQUIRED_CHANNEL_LINKS[chat_i]}\"><b>{REQUIRED_CHANNEL_NAMES[chat_i]}</b></a>\n"
    check_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "check"), callback_data=create_callback_start(2))
    markup = types.InlineKeyboardMarkup(inline_keyboard=[[check_button]])
    await send_message(message, msg, reply_markup=markup)
    if isinstance(message, types.CallbackQuery):
      await message.answer()
  else:
    await send_message(message, LanguageService.get_translation(language_code, "hello"), reply_markup=main_markup(language_code))

def main_markup(language_code: str):
  auto_buy = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "autobuy"), callback_data=create_callback_autobuy(0))
  accounts = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "accounts"), callback_data=create_callback_accounts(0))
  my_profile_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "profile"), callback_data=create_callback_profile(0))
  faq_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "faq"), url=FAQ_LINK)
  help_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "help"), callback_data=create_callback_start(1))

  channel_button = types.InlineKeyboardButton(text=CHANNEL_NAME, url=CHANNEL_LINK)
  return types.InlineKeyboardMarkup(inline_keyboard=[[auto_buy], [accounts, my_profile_button], [faq_button, help_button], [channel_button]])

async def support(callback: types.CallbackQuery):
  language_code = await UserService.get_language_code(callback.from_user.id)
  keyboard_builder = InlineKeyboardBuilder()

  keyboard_builder.button(text=LanguageService.get_translation(language_code, "support"), url=SUPPORT_LINK)
  keyboard_builder.add(get_back_to_menu_button(language_code))
  keyboard_builder.adjust(1)
  await send_message(callback, LanguageService.get_translation(language_code, "qa"), reply_markup=keyboard_builder.as_markup())

@start_router.callback_query(StartCallback.filter())
async def start_menu_navigation(callback: types.CallbackQuery, callback_data: StartCallback):
  current_level = callback_data.level

  levels = {
    0: start,
    1: support,
    2: check_subs
  }

  current_level_function = levels[current_level]
  await current_level_function(callback)