from typing import Union
from aiogram import types, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from handlers.common.common import send_message, send_to_admins
from aiogram.fsm.context import FSMContext
from config import BASE_RPC
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

payment_test_router = Router()

class PaymentTestCallback(CallbackData, prefix="payment_test"):
  level: int
  price: float
  asset_i: int

def create_payment_test_callback(level: int, price: float = -1, asset_i: int = -1):
  return PaymentTestCallback(level=level, price=price, asset_i=asset_i).pack()

async def payment_test(message: Union[Message, CallbackQuery]):
  from handlers.user.start import create_callback_start

  payment_test_0_usd_button = types.InlineKeyboardButton(text=f"0$ (test this before making any transfers)", callback_data=create_payment_test_callback(1, price=0))
  payment_test_5_usd_button = types.InlineKeyboardButton(text=f"5$", callback_data=create_payment_test_callback(1, price=5))
  payment_test_10_usd_button = types.InlineKeyboardButton(text=f"10$", callback_data=create_payment_test_callback(1, price=10))
  payment_test_25_usd_button = types.InlineKeyboardButton(text=f"25$", callback_data=create_payment_test_callback(1, price=25))
  payment_test_50_usd_button = types.InlineKeyboardButton(text=f"50$", callback_data=create_payment_test_callback(1, price=50))
  payment_test_100_usd_button = types.InlineKeyboardButton(text=f"100$", callback_data=create_payment_test_callback(1, price=100))
  back_button = types.InlineKeyboardButton(text="Back", callback_data=create_callback_start(0))
  markup = types.InlineKeyboardMarkup(inline_keyboard=[[
    payment_test_0_usd_button,
    payment_test_5_usd_button,
    payment_test_10_usd_button,
    payment_test_25_usd_button,
    payment_test_50_usd_button,
    payment_test_100_usd_button
  ], [back_button]])
  await send_message(message, "Select an amount", reply_markup=markup)

async def crypto_payment_selection(callback: CallbackQuery):
  unpacked_callback = PaymentTestCallback.unpack(callback.data)

  msg = (f"Select a crypto asset to use (<b>{unpacked_callback.price}$</b>)")

  markup = await get_crypto_payment_markup(unpacked_callback.price)
  await send_message(callback, msg, reply_markup=markup)

async def get_crypto_payment_markup(price: float):
  keyboard_builder = InlineKeyboardBuilder()
  option_buttons = []

  for asset_i, asset in enumerate(assets):
    display = f"{await asset.network} | {await asset.symbol}"
    option_buttons.append(types.InlineKeyboardButton(text=display, callback_data=create_payment_test_callback(2, price=price, asset_i=asset_i)))

  keyboard_builder.add(*option_buttons)
  back_button = types.InlineKeyboardButton(text="Back", callback_data=create_payment_test_callback(0))
  keyboard_builder.add(back_button)
  adj = len(option_buttons) * [1] + [1]
  keyboard_builder.adjust(*adj)
  
  return keyboard_builder.as_markup()

async def crypto_payment(callback: CallbackQuery, state: FSMContext):
  unpacked_callback = PaymentTestCallback.unpack(callback.data)

  asset = assets[unpacked_callback.asset_i]

  symbol = await asset.symbol
  price_usd = await asset.price_usd()
  deposit_amount = unpacked_callback.price / price_usd

  secret_key, public_key = await asset.create_wallet()
  msg = (f'<a href="{await asset.link}">{await asset.network} | {symbol}</a> (<b>Any other assets will be lost</b>)\n\n'
         f'Required deposit of <code>{round(deposit_amount, 6)}</code> <b>{symbol}</b>\n'
         f'Address: <code>{public_key}</code>')
  
  check_button = types.InlineKeyboardButton(text="Check", callback_data=create_payment_test_callback(3, price=unpacked_callback.price, asset_i=unpacked_callback.asset_i))
  cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data=create_payment_test_callback(0))
  markup = types.InlineKeyboardMarkup(inline_keyboard=[[check_button], [cancel_button]])
  await state.update_data(secret_key=secret_key, public_key=public_key, deposit_amount=deposit_amount)
  await send_message(callback, msg, reply_markup=markup)
  
async def check_payment(callback: CallbackQuery, state: FSMContext):
  from handlers.user.start import start

  data = await state.get_data()
  await state.clear()
  secret_key = data.get("secret_key")
  public_key = data.get("public_key")
  deposit_amount = data.get("deposit_amount")

  telegram_id = callback.from_user.id
  unpacked_callback = PaymentTestCallback.unpack(callback.data)

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
  await send_to_admins(admin_msg)
  return await start(callback)

@payment_test_router.callback_query(PaymentTestCallback.filter())
async def navigate(callback: CallbackQuery, state: FSMContext, callback_data: PaymentTestCallback):
  current_level = callback_data.level

  levels = {
    0: payment_test,
    1: crypto_payment_selection,
    2: crypto_payment,
    3: check_payment
  }

  current_level_function = levels[current_level]
  if inspect.getfullargspec(current_level_function).annotations.get("state") == FSMContext:
    await current_level_function(callback, state)
  else:
    await current_level_function(callback)