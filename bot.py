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

# ✅ Handle AI Signal button
@dp.callback_query(lambda c: c.data == "ai_signal")
async def ai_signal(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥇 Gold", callback_data="gold_signal")],
            [
                InlineKeyboardButton(text="₿ Bitcoin", callback_data="bitcoin_signal"),
                InlineKeyboardButton(text="📈 Dow Jones", callback_data="dowjones_signal"),
                InlineKeyboardButton(text="⚙️ ETH", callback_data="eth_signal")
            ],
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
    chat_id = callback_query.message.chat.id
    if chat_id not in subscribed_users:
        subscribed_users.add(chat_id)
        save_subscriptions()
        await callback_query.answer("✅ Subscribed to Gold Signals!")
        await bot.send_message(chat_id=chat_id, text="📩 You are now subscribed to Gold Signals. You will receive alerts automatically.")
    else:
        await callback_query.answer("✅ You are already subscribed!")

# ✅ Handle Unsubscribe from Gold Signals
@dp.callback_query(lambda c: c.data == "unsubscribe_gold")
async def unsubscribe_gold(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        save_subscriptions()
        await callback_query.answer("🚫 Unsubscribed from Gold Signals!")
        await bot.send_message(chat_id=chat_id, text="❌ You have unsubscribed from Gold Signals.")
    else:
        await callback_query.answer("⚠️ You are not subscribed!")

# ✅ Handle "Coming Soon" for other assets
@dp.callback_query(lambda c: c.data in ["bitcoin_signal", "dowjones_signal", "eth_signal"])
async def coming_soon(callback_query: types.CallbackQuery):
    await callback_query.answer("🚧 Coming Soon! 🚀", show_alert=True)

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
