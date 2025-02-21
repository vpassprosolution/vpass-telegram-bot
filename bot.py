import httpx
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
import uvicorn
from dotenv import load_dotenv

# ✅ Load bot token from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your .env file.")

WEBHOOK_URL = "WEBHOOK_URL = "https://web-production-ceec.up.railway.app/webhook"
"  # ✅ Replace with your actual Railway bot URL

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # ✅ Use MemoryStorage for proper callback handling

app = FastAPI()

SUBSCRIPTION_FILE = "subscribed_users.json"

# ✅ Load and save subscriptions for TradingView alerts
def load_subscriptions():
    if os.path.exists(SUBSCRIPTION_FILE):
        with open(SUBSCRIPTION_FILE, "r") as file:
            return set(json.load(file))
    return set()

def save_subscriptions():
    with open(SUBSCRIPTION_FILE, "w") as file:
        json.dump(list(subscribed_users), file)

subscribed_users = load_subscriptions()

# ✅ Handle /start command
@dp.message(Command("start"))
async def start_command(message: types.Message):
    chat_id = message.chat.id
    welcome_text = """Welcome to VPASS Pro – Your AI-Powered Trading Companion

At VPASS Pro, we redefine trading excellence through cutting-edge AI technology.
Our mission is to empower you with precise, real-time trading signals and actionable insights.
Explore the future of trading today. Let’s elevate your strategy together.
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Try VPASS Pro Now", callback_data="show_main_buttons")]
        ]
    )
    await bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=keyboard)

# ✅ Handle "Try VPASS Pro Now" button
@dp.callback_query(lambda c: c.data == "show_main_buttons")
async def show_main_buttons(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 AI Signal", callback_data="ai_signal")],
            [
                InlineKeyboardButton(text="🌍 Forex Factory", url="https://www.forexfactory.com/"),
                InlineKeyboardButton(text="🔍 Deepseek", url="https://www.deepseek.com/")
            ],
            [
                InlineKeyboardButton(text="💬 Discord", url="https://discord.com/"),
                InlineKeyboardButton(text="🤖 ChatGPT", url="https://chatgpt.com/")
            ]
        ]
    )
    await callback_query.message.edit_text("Access Your Exclusive Trading Tools:", reply_markup=keyboard)

# ✅ Handle AI Signal button
@dp.callback_query(lambda c: c.data == "ai_signal")
async def ai_signal(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥇 Gold", callback_data="gold_signal")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="show_main_buttons")]
        ]
    )
    await callback_query.message.edit_text("Choose Your Instrument:", reply_markup=keyboard)

# ✅ Handle Gold signal button
@dp.callback_query(lambda c: c.data == "gold_signal")
async def gold_signal(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📩 Subscribe Gold Signal", callback_data="subscribe_gold"),
                InlineKeyboardButton(text="🚫 Unsubscribe Gold Signal", callback_data="unsubscribe_gold")
            ],
            [InlineKeyboardButton(text="🔙 Back", callback_data="ai_signal")]
        ]
    )
    await callback_query.message.edit_text("Gold Signal Options:", reply_markup=keyboard)

# ✅ Handle Subscribe to Gold Signals
@dp.callback_query(lambda c: c.data == "subscribe_gold")
async def subscribe_gold(callback_query: types.CallbackQuery):
    chat_id = str(callback_query.message.chat.id)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://tradingviewwebhook-production.up.railway.app/subscribe",
            json={"user_id": chat_id}
        )
    if response.status_code == 200:
        await callback_query.answer("✅ Subscribed to Gold Signals!")
        await bot.send_message(chat_id=chat_id, text="📩 You are now subscribed to Gold Signals.")
    else:
        await callback_query.answer("❌ Subscription failed. Try again later.")

# ✅ Handle Unsubscribe from Gold Signals
@dp.callback_query(lambda c: c.data == "unsubscribe_gold")
async def unsubscribe_gold(callback_query: types.CallbackQuery):
    chat_id = str(callback_query.message.chat.id)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://tradingviewwebhook-production.up.railway.app/unsubscribe",
            json={"user_id": chat_id}
        )
    if response.status_code == 200:
        await callback_query.answer("🚫 Unsubscribed from Gold Signals!")
        await bot.send_message(chat_id=chat_id, text="❌ You have unsubscribed from Gold Signals.")
    else:
        await callback_query.answer("❌ Unsubscription failed. Try again later.")

# ✅ Webhook for Telegram Updates
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    update_obj = types.Update(**update)
    await dp.feed_update(bot, update_obj)
    return {"status": "ok"}

# ✅ Handle TradingView alerts and forward to subscribers
@app.post("/tradingview")
async def tradingview_alert(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "🔔 New TradingView Alert!")

        if not subscribed_users:
            logging.info("⚠️ No users are subscribed, skipping message.")
            return {"status": "no_subscribers"}

        for user in subscribed_users:
            try:
                await bot.send_message(chat_id=user, text=message)
                logging.info(f"✅ Sent TradingView alert to {user}")
            except Exception as e:
                logging.error(f"❌ Failed to send message to {user}: {e}")

        return {"status": "success", "sent_to": len(subscribed_users)}

    except Exception as e:
        logging.error(f"❌ Error receiving TradingView alert: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Set webhook on startup
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"🚀 Webhook set: {WEBHOOK_URL}")

# ✅ Remove webhook on shutdown
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logging.info("🛑 Webhook removed")

# ✅ Run FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
