import asyncio
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
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

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # ✅ Use MemoryStorage for proper callback handling

app = FastAPI(lifespan=None)  # ✅ Disable lifespan warning

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

    video_path = "videos/welcome.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await bot.send_video(chat_id=chat_id, video=video, supports_streaming=True)
    else:
        logging.error(f"❌ Video not found: {video_path}")
        await message.answer("⚠️ Welcome video not found. Please contact support.")

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

# ✅ Handle TradingView webhook alerts
@app.post("/tradingview")
async def tradingview_alert(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "🔔 New TradingView Alert!")
        for user in subscribed_users:
            try:
                await bot.send_message(chat_id=user, text=message)
            except Exception as e:
                logging.error(f"❌ Failed to send message to {user}: {e}")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"❌ Error receiving TradingView alert: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Run Telegram bot and FastAPI server together
async def start_bot():
    print("🤖 Telegram Bot is Running...")
    await dp.start_polling(bot)

async def start_api():
    print("🌍 FastAPI Server is Running...")
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)), loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    task1 = asyncio.create_task(start_bot())
    task2 = asyncio.create_task(start_api())
    await asyncio.gather(task1, task2)  # ✅ Run both services together

if __name__ == "__main__":
    asyncio.run(main())
