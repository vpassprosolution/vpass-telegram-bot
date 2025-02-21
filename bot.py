import asyncio
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from fastapi import FastAPI, Request
import uvicorn
from dotenv import load_dotenv

# ✅ Debugging Message
print("🚀 VPASS Pro Bot is starting...")

# ✅ Load bot token from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your .env file.")

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)

# ✅ Initialize Telegram Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Initialize FastAPI without lifespan warning
app = FastAPI(lifespan=None)

# ✅ Subscription Data Storage
SUBSCRIPTION_FILE = "subscribed_users.json"

def load_subscriptions():
    """Load subscribed users from file."""
    if os.path.exists(SUBSCRIPTION_FILE):
        with open(SUBSCRIPTION_FILE, "r") as file:
            return set(json.load(file))
    return set()

def save_subscriptions():
    """Save subscribed users to file."""
    with open(SUBSCRIPTION_FILE, "w") as file:
        json.dump(list(subscribed_users), file)

subscribed_users = load_subscriptions()

# ✅ Telegram Bot Handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    chat_id = message.chat.id
    welcome_text = """Welcome to VPASS Pro – Your AI-Powered Trading Companion

At VPASS Pro, we redefine trading excellence through cutting-edge AI technology.
Our mission is to empower you with precise, real-time trading signals and actionable insights.
Explore the future of trading today. Let’s elevate your strategy together.
"""

    # ✅ Send Welcome Video
    video_path = "videos/welcome.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await bot.send_video(chat_id=chat_id, video=video, supports_streaming=True)
    else:
        logging.error(f"❌ Video not found: {video_path}")
        await message.answer("⚠️ Welcome video not found. Please contact support.")

    # ✅ Show Main Menu Button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Try VPASS Pro Now", callback_data="show_main_buttons")]
        ]
    )
    await bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=keyboard)

# ✅ TradingView Webhook Handler
@app.post("/tradingview")
async def tradingview_alert(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "🔔 New TradingView Alert!")

        # ✅ Send alerts only to subscribed users
        for user in subscribed_users:
            try:
                await bot.send_message(chat_id=user, text=message)
            except Exception as e:
                logging.error(f"❌ Failed to send message to {user}: {e}")
        
        return {"status": "success"}
    
    except Exception as e:
        logging.error(f"❌ Error receiving TradingView alert: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Start Bot and API Together
async def start_bot():
    print("🤖 Telegram Bot is Running...")
    await dp.start_polling(bot)

import uvicorn

async def start_api():
    print("🌍 Starting FastAPI Server...")
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    task1 = asyncio.create_task(start_bot())
    task2 = asyncio.create_task(start_api())
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())  # ✅ Start Everything Together
