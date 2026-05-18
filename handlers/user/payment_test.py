from typing import Union
from aiogram import types, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from utils.custom_filters import IsUserExistFilter
from aiogram.types import CallbackQuery, Message
from handlers.common.common import send_message, send_to_admins
from aiogram.fsm.context import FSMContext
from config import PRICE_30_DAYS, BASE_RPC
from services.user import UserService
from language import LanguageService
from crypto_api.TRC20 import TRC20
from crypto_api.BEP20 import BEP20
from crypto_api.ERC20 import ERC20
import asyncio
import inspect
import logging

logger = logging.getLogger(__name__)

assets = [
  ERC20(BASE_RPC, "USDC", "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", "https://basescan.org/token/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", "BASE"),
  BEP20("USDT", "0x55d398326f99059fF775485246999027B3197955"),
  TRC20("USDT", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"),
]

payment_router = Router()

class SubscriptionCallback(CallbackData, prefix="subscription"):
  level: int
  price: float
  asset_i: int

def create_callback_subscription(level: int, price: float = -1, asset_i: int = -1):
  return SubscriptionCallback(level=level, price=price, asset_i=asset_i).pack()

async def subscription(message: Union[Message, CallbackQuery]):
  from handlers.user.my_profile import create_callback_profile

  telegram_id = message.chat.id if isinstance(message, Message) else message.from_user.id
  language_code = await UserService.get_language_code(telegram_id)
  
  msg = LanguageService.get_translation(language_code, "subscription_selection")
  days = LanguageService.get_translation(language_code, "days")
  subscription_30_days_button = types.InlineKeyboardButton(text=f"30 {days} | {PRICE_30_DAYS}$", callback_data=create_callback_subscription(1, price=PRICE_30_DAYS))
  back_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "back"), callback_data=create_callback_profile(0))
  markup = types.InlineKeyboardMarkup(inline_keyboard=[[subscription_30_days_button], [back_button]])
  await send_message(message, msg, reply_markup=markup)

async def crypto_payment_selection(callback: CallbackQuery):
  telegram_id = callback.from_user.id
  language_code = await UserService.get_language_code(telegram_id)
  unpacked_callback = SubscriptionCallback.unpack(callback.data)

  crypto_selection = LanguageService.get_translation(language_code, "crypto_selection")
  msg = (f"{crypto_selection} (<b>{unpacked_callback.price}$</b>)")

  markup = await get_crypto_payment_markup(unpacked_callback.price, language_code)
  await send_message(callback, msg, reply_markup=markup)

async def get_crypto_payment_markup(price: float, language_code: str):
  keyboard_builder = InlineKeyboardBuilder()
  option_buttons = []

  for asset_i, asset in enumerate(assets):
    display = f"{await asset.network} | {await asset.symbol}"
    option_buttons.append(types.InlineKeyboardButton(text=display, callback_data=create_callback_subscription(2, price=price, asset_i=asset_i)))

  keyboard_builder.add(*option_buttons)
  back_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "back"), callback_data=create_callback_subscription(0))
  keyboard_builder.add(back_button)
  adj = len(option_buttons) * [1] + [1]
  keyboard_builder.adjust(*adj)
  
  return keyboard_builder.as_markup()

async def crypto_payment(callback: CallbackQuery, state: FSMContext):
  telegram_id = callback.from_user.id
  language_code = await UserService.get_language_code(telegram_id)
  unpacked_callback = SubscriptionCallback.unpack(callback.data)

  asset = assets[unpacked_callback.asset_i]

  crypto_deposit_warning = LanguageService.get_translation(language_code, "crypto_deposit_warning")
  crypto_deposit_amount = LanguageService.get_translation(language_code, "crypto_deposit_amount")
  crypto_address = LanguageService.get_translation(language_code, "crypto_address")
  symbol = await asset.symbol
  price_usd = await asset.price_usd()
  deposit_amount = unpacked_callback.price / price_usd

  secret_key, public_key = await asset.create_wallet()
  msg = (f'<a href="{await asset.link}">{await asset.network} | {symbol}</a> {crypto_deposit_warning}\n\n'
         f'{crypto_deposit_amount}<code>{round(deposit_amount, 6)}</code> <b>{symbol}</b>\n'
         f'{crypto_address}: <code>{public_key}</code>')
  
  check_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "check"), callback_data=create_callback_subscription(3, price=unpacked_callback.price, asset_i=unpacked_callback.asset_i))
  cancel_button = types.InlineKeyboardButton(text=LanguageService.get_translation(language_code, "cancel"), callback_data=create_callback_subscription(0))
  markup = types.InlineKeyboardMarkup(inline_keyboard=[[check_button], [cancel_button]])
  await state.update_data(secret_key=secret_key, public_key=public_key, deposit_amount=deposit_amount)
  await send_message(callback, msg, reply_markup=markup)
  
async def check_payment(callback: CallbackQuery, state: FSMContext):
  from handlers.user.my_profile import my_profile

  data = await state.get_data()
  await state.clear()
  secret_key = data.get("secret_key")
  public_key = data.get("public_key")
  deposit_amount = data.get("deposit_amount")

  telegram_id = callback.from_user.id
  unpacked_callback = SubscriptionCallback.unpack(callback.data)

  asset = assets[unpacked_callback.asset_i]

  balance = await asset.get_balance(public_key)
  if balance < deposit_amount:
    await state.update_data(secret_key=secret_key, public_key=public_key, deposit_amount=deposit_amount)
    await callback.answer()
    return

  symbol = await asset.symbol
  admin_msg = (f'<b>Payment</b> for {deposit_amount} <a href="{await asset.link}">{await asset.network} | {symbol}</a>\n\n'
               f'ID: <code>{telegram_id}</code>\n'
               f'Username: <b>{callback.from_user.username or "unknown"}</b>\n'
               f'Wallet: <span class=\"tg-spoiler\">{secret_key}</span>')
  await asyncio.gather(send_to_admins(admin_msg), UserService.subscribe_user_for_3_months(telegram_id))
  return await my_profile(callback)

@payment_router.callback_query(SubscriptionCallback.filter(), IsUserExistFilter())
async def navigate(callback: CallbackQuery, state: FSMContext, callback_data: SubscriptionCallback):
  current_level = callback_data.level

  levels = {
    0: subscription,
    1: crypto_payment_selection,
    2: crypto_payment,
    3: check_payment
  }

  current_level_function = levels[current_level]
  if inspect.getfullargspec(current_level_function).annotations.get("state") == FSMContext:
    await current_level_function(callback, state)
  else:
    await current_level_function(callback)