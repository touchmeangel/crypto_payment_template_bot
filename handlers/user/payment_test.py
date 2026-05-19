from aiogram import F, Router, types
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BASE_RPC
from crypto_api.BEP20 import BEP20
from crypto_api.ERC20 import ERC20
from crypto_api.TRC20 import TRC20
from handlers.common.common import send_message, send_to_admins

# ==========================================
# 1. ASSET CONFIGURATION
# ==========================================
assets = [
    ERC20(
        BASE_RPC,
        "USDC",
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "https://basescan.org/token/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "BASE",
    ),
    BEP20("USDT", "0x55d398326f99059fF775485246999027B3197955"),
    TRC20("USDT", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"),
]

payment_test_router = Router()


# ==========================================
# 2. CALLBACK FACTORY
# ==========================================
class PaymentTestCallback(CallbackData, prefix="payment_test"):
    level: int  # 0: Select Price, 1: Select Crypto, 2: Invoice Info, 3: Verify
    price: float
    asset_i: int


# ==========================================
# 3. PAYMENT FLOW HANDLERS
# ==========================================


# LEVEL 0: Select USD Amount
@payment_test_router.callback_query(PaymentTestCallback.filter(F.level == 0))
async def payment_test(event: CallbackQuery | Message):
    """Displays the initial USD package pricing options."""
    from handlers.user.start import create_callback_start

    builder = InlineKeyboardBuilder()

    # 1. Add the 0$ test button
    builder.add(
        types.InlineKeyboardButton(
            text="0$ (Test Transfer)",
            callback_data=PaymentTestCallback(level=1, price=0, asset_i=-1).pack(),
        )
    )

    # 2. Add the regular price buttons to the pool
    for amount in [5, 10, 25, 50, 100]:
        builder.add(
            types.InlineKeyboardButton(
                text=f"{amount}$",
                callback_data=PaymentTestCallback(
                    level=1, price=amount, asset_i=-1
                ).pack(),
            )
        )

    # 3. Shape the grid: 1 button for the first row, then rows of max 3 buttons
    builder.adjust(1, 3)

    # 4. Force the Back button onto its own new row at the very bottom
    builder.row(
        types.InlineKeyboardButton(text="Back", callback_data=create_callback_start(0))
    )

    await send_message(event, "Select an amount:", reply_markup=builder.as_markup())


# LEVEL 1: Select Cryptocurrency Network
@payment_test_router.callback_query(PaymentTestCallback.filter(F.level == 1))
async def crypto_payment_selection(
    callback: CallbackQuery, callback_data: PaymentTestCallback
):
    """Renders available coin/network configurations based on the chosen price."""
    builder = InlineKeyboardBuilder()

    for idx, asset in enumerate(assets):
        display = f"{await asset.network} | {await asset.symbol}"
        builder.row(
            types.InlineKeyboardButton(
                text=display,
                callback_data=PaymentTestCallback(
                    level=2, price=callback_data.price, asset_i=idx
                ).pack(),
            )
        )

    builder.row(
        types.InlineKeyboardButton(
            text="Back",
            callback_data=PaymentTestCallback(level=0, price=0, asset_i=-1).pack(),
        )
    )

    msg = f"Select a crypto asset to use (<b>{callback_data.price}$</b>)"
    await send_message(callback, msg, reply_markup=builder.as_markup())
    await callback.answer()


# LEVEL 2: Generate Temporary Wallet & Show Invoice Instructions
@payment_test_router.callback_query(PaymentTestCallback.filter(F.level == 2))
async def crypto_payment(
    callback: CallbackQuery, callback_data: PaymentTestCallback, state: FSMContext
):
    """Generates an address, calculates exchange rate, and provisions temporary FSM context data."""
    asset = assets[callback_data.asset_i]
    symbol = await asset.symbol
    price_usd = await asset.price_usd()

    deposit_amount = round(callback_data.price / price_usd, 6)
    secret_key, public_key = await asset.create_wallet()

    msg = (
        f'<a href="{await asset.link}">{await asset.network} | {symbol}</a> (<b>Any other assets will be lost</b>)\n\n'
        f"Required deposit of <code>{deposit_amount}</code> <b>{symbol}</b>\n"
        f"Address: <code>{public_key}</code>"
    )

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Check",
                    callback_data=PaymentTestCallback(
                        level=3,
                        price=callback_data.price,
                        asset_i=callback_data.asset_i,
                    ).pack(),
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="Cancel",
                    callback_data=PaymentTestCallback(
                        level=0, price=0, asset_i=-1
                    ).pack(),
                )
            ],
        ]
    )

    # Store dynamic transaction records securely inside state cache
    await state.update_data(
        secret_key=secret_key, public_key=public_key, deposit_amount=deposit_amount
    )
    await send_message(callback, msg, reply_markup=markup)
    await callback.answer()


# LEVEL 3: Verification Engine
@payment_test_router.callback_query(PaymentTestCallback.filter(F.level == 3))
async def check_payment(
    callback: CallbackQuery, callback_data: PaymentTestCallback, state: FSMContext
):
    """Checks the blockchain for incoming transaction matching the required FSM state metrics."""
    from handlers.user.start import start

    data = await state.get_data()
    secret_key = data.get("secret_key")
    public_key = data.get("public_key")
    deposit_amount = data.get("deposit_amount")

    asset = assets[callback_data.asset_i]
    balance = await asset.get_balance(public_key)

    # Fast-return loop fallback if the user hasn't deposited yet
    if balance < deposit_amount:
        await callback.answer(
            "Payment not found yet. Please try again in a few moments.", show_alert=True
        )
        return

    # Successful payment: wipe active state tracking & notify administration
    await state.clear()
    symbol = await asset.symbol
    admin_msg = (
        f"<b>💰 Successful Payment Received</b>\n"
        f'Asset: <a href="{await asset.link}">{await asset.network} | {symbol}</a>\n'
        f"Amount: <code>{deposit_amount}</code>\n"
        f"User ID: <code>{callback.from_user.id}</code>\n"
        f"Username: @{callback.from_user.username or 'unknown'}\n"
        f'Wallet Key: <span class="tg-spoiler">{secret_key}</span>'
    )

    await send_to_admins(admin_msg)
    await callback.answer("Payment verified successfully!")
    return await start(callback)
