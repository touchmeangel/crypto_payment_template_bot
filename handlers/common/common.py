import logging
import traceback
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from language import LanguageService
from config import ADMIN_ID_LIST
from bot import bot

logger = logging.getLogger(__name__)

async def send_message(message: types.Message | types.CallbackQuery, content: str, reply_markup: types.InlineKeyboardMarkup | None = None):
  telegram_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id

  try:
    if isinstance(message, types.Message):
      await message.answer(content, reply_markup=reply_markup, disable_web_page_preview=True)
    if isinstance(message, types.CallbackQuery):
      await message.message.edit_text(content, reply_markup=reply_markup, disable_web_page_preview=True)
  except Exception as e:
    tb_str = traceback.format_exc()
    logger.warning(f"[{telegram_id}] failed to send message: {e} / {tb_str}")

async def send_to_admins(content: str):
  for admin in ADMIN_ID_LIST:
    try:
      await bot.send_message(admin, content, disable_web_page_preview=True)
    except Exception as e:
      logging.warning(e)

def add_pagination_buttons(keyboard_builder: InlineKeyboardBuilder, unpacked_callback, last_page, add_buttons, translations) -> InlineKeyboardBuilder:
    buttons = []
    if unpacked_callback.page > 0:
        back_page_callback = unpacked_callback.__copy__()
        back_page_callback.page -= 1
        first_page_callback = unpacked_callback.__copy__()
        first_page_callback.page = 0
        buttons.append(types.InlineKeyboardButton(text=translations["first"], callback_data=first_page_callback.pack()))
        buttons.append(types.InlineKeyboardButton(text=translations["previous"], callback_data=back_page_callback.pack()))
    if unpacked_callback.page < last_page:
        last_page_callback = unpacked_callback.__copy__()
        last_page_callback.page = last_page
        unpacked_callback.page += 1
        buttons.append(types.InlineKeyboardButton(text=translations["next"],
                                                  callback_data=unpacked_callback.pack()))
        buttons.append(types.InlineKeyboardButton(text=translations["last"], callback_data=last_page_callback.pack()))
    keyboard_builder.row(*buttons)
    for add_button in add_buttons:
        keyboard_builder.row(add_button)
    return keyboard_builder

def get_back_to_menu_button(language_code: str):
    from handlers.user.start import create_callback_start
    return types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "back"), callback_data=create_callback_start(0))

def get_back_to_menu_markup(language_code: str):
    return types.InlineKeyboardMarkup(inline_keyboard=[[get_back_to_menu_button(language_code)]])