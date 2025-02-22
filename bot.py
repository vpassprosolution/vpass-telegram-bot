import httpx
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
from aiogram.types import FSInputFile
import uvicorn
import asyncio
from dotenv import load_dotenv

# ✅ Load bot token from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your .env file.")

# ✅ Define Webhook URL - Ensure it's the correct Railway bot service URL
WEBHOOK_URL = "https://web-production-ceec.up.railway.app/webhook"

# ✅ Setup logging for debugging
logging.basicConfig(level=logging.INFO)

# ✅ Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  

# ✅ Initialize FastAPI
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
    
    # Send the welcome image first
    image_path = "welcome.png"  # Ensure this file is in the same folder as bot.py
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id=chat_id, photo=photo)
    else:
        logging.warning("Welcome image not found!")
    
    # Send the welcome message
    welcome_text = """Welcome to VPASS PRO version 2.0 
Your AI-Powered Trading Companion Your exclusive AI assistant, designed for those who value efficiency and sophistication.
From smart solutions to seamless interactions,VPass Pro delivers premium support tailored just for you.
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Try VPASS Pro Now", callback_data="show_main_buttons")]
        ]
    )
    await bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=keyboard)

# ✅ Define the list of allowed admins (Your Telegram User ID)
ADMIN_IDS = {"6756668018"}  # 🔹 You are now the admin!

# ✅ Load allowed users from service.json (Store Usernames)
SERVICE_FILE = "service.json"

def load_allowed_users():
    if os.path.exists(SERVICE_FILE):
        with open(SERVICE_FILE, "r") as file:
            data = json.load(file)
            return set(data.get("allowed_users", []))  # Load usernames from JSON
    return set()

def save_allowed_users():
    with open(SERVICE_FILE, "r") as file:
        data = json.load(file)
    
    data["allowed_users"] = list(allowed_users)

    with open(SERVICE_FILE, "w") as file:
        json.dump(data, file, indent=4)

allowed_users = load_allowed_users()

# ✅ Handle /admin command (Admin Panel)
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    chat_id = str(message.chat.id)

    # Check if user is an admin
    if chat_id not in ADMIN_IDS:
        await message.reply("❌ You are not authorized to use this command.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add User", callback_data="add_user")],
            [InlineKeyboardButton(text="❌ Remove User", callback_data="remove_user")],
            [InlineKeyboardButton(text="📜 List Users", callback_data="list_users")],
            [InlineKeyboardButton(text="🔍 Check User", callback_data="check_user")]
        ]
    )
    await message.reply("⚙️ Admin Panel", reply_markup=keyboard)

# ✅ Handle "Add User" (Using Username)
@dp.callback_query(lambda c: c.data == "add_user")
async def add_user_prompt(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("✏️ Send the **username** of the user to add (without @).")

@dp.message(lambda message: message.text and message.text.startswith("add "))
async def add_user(message: types.Message):
    chat_id = str(message.chat.id)
    if chat_id not in ADMIN_IDS:
        return

    username = message.text.replace("add ", "").strip().lower()
    
    if username in allowed_users:
        await message.reply(f"✅ @{username} is already allowed!")
    else:
        allowed_users.add(username)
        save_allowed_users()
        await message.reply(f"✅ @{username} has been **added** to the allowed users!")

# ✅ Handle "Remove User" (Using Username)
@dp.callback_query(lambda c: c.data == "remove_user")
async def remove_user_prompt(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("✏️ Send the **username** of the user to remove.")

@dp.message(lambda message: message.text and message.text.startswith("remove "))
async def remove_user(message: types.Message):
    chat_id = str(message.chat.id)
    if chat_id not in ADMIN_IDS:
        return

    username = message.text.replace("remove ", "").strip().lower()

    if username in allowed_users:
        allowed_users.remove(username)
        save_allowed_users()
        await message.reply(f"❌ @{username} has been **removed** from the allowed users!")
    else:
        await message.reply(f"⚠️ @{username} is not in the allowed users list!")

# ✅ Handle "List Users" (Show Usernames)
@dp.callback_query(lambda c: c.data == "list_users")
async def list_users(callback_query: types.CallbackQuery):
    if not allowed_users:
        await callback_query.message.edit_text("📜 No allowed users found.")
    else:
        user_list = "\n".join(f"✅ @{user}" for user in allowed_users)
        await callback_query.message.edit_text(f"📜 **Allowed Users:**\n\n{user_list}")

# ✅ Handle "Check User" (Using Username)
@dp.callback_query(lambda c: c.data == "check_user")
async def check_user_prompt(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("✏️ Send the **username** to check.")

@dp.message(lambda message: message.text and message.text.startswith("check "))
async def check_user(message: types.Message):
    chat_id = str(message.chat.id)
    if chat_id not in ADMIN_IDS:
        return

    username = message.text.replace("check ", "").strip().lower()

    if username in allowed_users:
        await message.reply(f"✅ @{username} is **allowed** to use the bot!")
    else:
        await message.reply(f"❌ @{username} is **NOT** allowed to use the bot.")

# ✅ Restrict bot usage to allowed users (Check Username)
@dp.message()
async def restrict_usage(message: types.Message):
    username = message.from_user.username.lower() if message.from_user.username else None
    if username not in allowed_users:
        await message.reply("❌ You are not authorized to use this bot.")




# ✅ Handle "Try VPASS Pro Now" button
@dp.callback_query(lambda c: c.data == "show_main_buttons")
async def show_main_buttons(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 VPASS SMART SIGNAL", callback_data="ai_signal")],
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
    await callback_query.message.edit_text("⬇️Access Your Exclusive Trading Tools⬇️", reply_markup=keyboard)

# ✅ Handle AI Signal button
@dp.callback_query(lambda c: c.data == "ai_signal")
async def ai_signal(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Gold", callback_data="gold_signal")],
            [
                InlineKeyboardButton(text="📈 Bitcoin", callback_data="bitcoin_signal"),
                InlineKeyboardButton(text="📈 Ethereum", callback_data="eth_signal")
            ],
            [
                InlineKeyboardButton(text="📈 Dow Jones", callback_data="dowjones_signal"),
                InlineKeyboardButton(text="📈 NASDAQ", callback_data="nasdaq_signal")
            ],
            [
                InlineKeyboardButton(text="📈 EUR/USD", callback_data="eurusd_signal"),
                InlineKeyboardButton(text="📊 GBP/USD", callback_data="gbpusd_signal")
            ],
            [InlineKeyboardButton(text="🔙 Back", callback_data="show_main_buttons")]
        ]
    )
    await callback_query.message.edit_text(" Choose Your Favorite Instruments ", reply_markup=keyboard)

# ✅ Function to create subscribe/unsubscribe keyboard
async def instrument_signal(callback_query: types.CallbackQuery, instrument: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"📩 Subscribe {instrument} Signal", callback_data=f"subscribe_{instrument}"),
                InlineKeyboardButton(text=f"🚫 Unsubscribe {instrument} Signal", callback_data=f"unsubscribe_{instrument}")
            ],
            [InlineKeyboardButton(text="🔙 Back", callback_data="ai_signal")]
        ]
    )
    await callback_query.message.edit_text(f"{instrument} Signal Options:", reply_markup=keyboard)

# ✅ Handle different instrument buttons
@dp.callback_query(lambda c: c.data in ["gold_signal", "bitcoin_signal", "eth_signal", "dowjones_signal", "nasdaq_signal", "eurusd_signal", "gbpusd_signal"])
async def instrument_signal_handler(callback_query: types.CallbackQuery):
    instrument_mapping = {
        "gold_signal": "Gold",
        "bitcoin_signal": "Bitcoin",
        "eth_signal": "Ethereum",
        "dowjones_signal": "Dow Jones",
        "nasdaq_signal": "NASDAQ",
        "eurusd_signal": "EUR/USD",
        "gbpusd_signal": "GBP/USD"
    }
    instrument = instrument_mapping.get(callback_query.data, "Unknown")
    await instrument_signal(callback_query, instrument)

# ✅ Handle Subscribe to Signals (with disappearing effect)
@dp.callback_query(lambda c: c.data.startswith("subscribe_"))
async def subscribe_signal(callback_query: types.CallbackQuery):
    chat_id = str(callback_query.message.chat.id)
    instrument = callback_query.data.replace("subscribe_", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://tradingviewwebhook-production.up.railway.app/subscribe",
            json={"user_id": chat_id, "instrument": instrument}
        )
    
    if response.status_code == 200:
        sent_message = await bot.send_message(chat_id=chat_id, text=f"✅ Subscribed to {instrument} Signals!")
        await asyncio.sleep(3)  # Wait 3 seconds
        await bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
    else:
        await callback_query.answer("❌ Subscription failed. Try again later.")

# ✅ Handle Unsubscribe from Signals (with disappearing effect)
@dp.callback_query(lambda c: c.data.startswith("unsubscribe_"))
async def unsubscribe_signal(callback_query: types.CallbackQuery):
    chat_id = str(callback_query.message.chat.id)
    instrument = callback_query.data.replace("unsubscribe_", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://tradingviewwebhook-production.up.railway.app/unsubscribe",
            json={"user_id": chat_id, "instrument": instrument}
        )
    
    if response.status_code == 200:
        sent_message = await bot.send_message(chat_id=chat_id, text=f"🚫 Unsubscribed from {instrument} Signals!")
        await asyncio.sleep(3)  # Wait 3 seconds
        await bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
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
