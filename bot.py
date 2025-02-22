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
import yfinance as yf 


# AI Super Agent API URL
AI_SUPER_AGENT_URL = "https://aisuperagent-production.up.railway.app/ai-signal"

# Function to fetch AI trading signals
async def get_ai_signal():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AI_SUPER_AGENT_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return f"⚠️ AI Super Agent Error: {data['error']}"
                
                # Format the response message
                message = f"""
📊 **AI Super Agent Signal for XAUUSD**  

💰 **Gold Price:** {data['gold_price']}  
📈 **Trend:** {data['trend']}  
✅ **Decision:** {data['decision']}  
⛔ **Stop Loss:** {data['stop_loss']}  
🎯 **Take Profit:** {data['take_profit']}  
"""
                return message
            else:
                return "⚠️ AI Super Agent is not responding. Please try again later."
    except Exception as e:
        return f"⚠️ Error fetching AI signal: {str(e)}"


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

@dp.callback_query(lambda c: c.data.startswith("unsubscribe_signal_"))
async def unsubscribe_from_signal(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id

    # ✅ Remove user from the subscription list
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        save_subscriptions()
        await callback_query.message.edit_text("🚫 You have been unsubscribed from AI signals.")
    else:
        await callback_query.message.answer("⚠️ You are not currently subscribed.")

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
            [InlineKeyboardButton(text="🤖 AI Super Agent", callback_data="ai_super_agent")],  # ✅ Added AI Super Agent button
            [InlineKeyboardButton(text="📈 AI Market Analysis", callback_data="market_analysis")],
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
    await callback_query.message.edit_text("⬇️ Access Your Exclusive Trading Tools ⬇️", reply_markup=keyboard)


# Handle AI Super Agent Button Click
@dp.callback_query(lambda c: c.data == "ai_super_agent")
async def ai_super_agent(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id

    # ✅ Step 1: Send "Fetching AI Super Agent recommendation..." message
    waiting_message = await bot.send_message(chat_id, "🔍 Fetching AI Super Agent recommendation... Please wait.")

    # ✅ Step 2: Fetch AI recommendation
    ai_signal_message = await get_ai_signal()
    
    # ✅ Step 3: Send AI Signal Result with "Start Again" Button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]
        ]
    )

    await asyncio.sleep(2)  # ✅ Wait 2 seconds to make it look smooth before deleting

    # ✅ Step 4: Delete ONLY the "Fetching AI recommendation..." message
    try:
        await bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
    except Exception:
        pass  # Ignore error if the message was already deleted

    # ✅ Step 5: Finally, send the AI recommendation (This will stay!)
    await bot.send_message(chat_id=chat_id, text=ai_signal_message, parse_mode="Markdown", reply_markup=keyboard)





# ✅ Handle AI Market Analysis Button
@dp.callback_query(lambda c: c.data == "market_analysis")
async def market_analysis(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🥇 Gold", callback_data="analyze_gold"),
                InlineKeyboardButton(text="₿ Bitcoin", callback_data="analyze_bitcoin")
            ],
            [
                InlineKeyboardButton(text="💹 EUR/USD", callback_data="analyze_eurusd"),
                InlineKeyboardButton(text="📊 NASDAQ", callback_data="analyze_nasdaq")
            ],
            [InlineKeyboardButton(text="🔙 Back", callback_data="show_main_buttons")]
        ]
    )
    await callback_query.message.edit_text("📊 Choose an instrument for AI analysis:", reply_markup=keyboard)

# ✅ Fetch & Analyze Market Data
async def get_market_analysis(instrument: str):
    symbols = {
        "gold": "GC=F",       # Gold Futures
        "bitcoin": "BTC-USD", # Bitcoin
        "eurusd": "EURUSD=X", # EUR/USD Forex
        "nasdaq": "^IXIC"     # NASDAQ Index
    }
    
    ticker = symbols.get(instrument.lower())
    
    if not ticker:
        return "⚠️ Invalid instrument selected."
    
    # Fetch latest market data
    try:
        df = yf.download(ticker, period="1d", interval="5m")  # ✅ Ensure df is initialized

        if df.empty:  # ✅ Check if DataFrame is empty correctly
            logging.error(f"No market data available for {ticker}.")
            return "⚠️ Market data not available. Try again later."

        # Ensure there are enough rows before accessing indices
        if len(df) < 3:
            logging.error(f"Not enough market data for {ticker}.")
            return "⚠️ Not enough market data to analyze trends."

        # ✅ Convert to floats correctly
        latest_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2])
        prev_prev_price = float(df["Close"].iloc[-3])

        price_change = latest_price - prev_price
        percent_change = (price_change / prev_price) * 100

        # ✅ Ensure only valid numbers are used in the condition
        if latest_price > prev_price > prev_prev_price:  
            trend = "Bullish"
        elif latest_price < prev_price < prev_prev_price:
            trend = "Bearish"
        else:
            trend = "Neutral"

        # AI-Based Recommendation
        if trend == "Bullish":
            recommendation = "🔼 **Buy** (Uptrend Detected)"
            stop_loss = round(latest_price - 2, 2)
            take_profit = round(latest_price + 4, 2)
        elif trend == "Bearish":
            recommendation = "🔽 **Sell** (Downtrend Detected)"
            stop_loss = round(latest_price + 2, 2)
            take_profit = round(latest_price - 4, 2)
        else:
            recommendation = "⚖️ **Hold** (Sideways Market)"
            stop_loss = None
            take_profit = None

        # ✅ Fix string formatting by using properly converted float values
        response = (
            f"📊 **{instrument.upper()} Market Analysis**\n\n"
            f"💰 **Latest Price**: {latest_price:.2f} USD\n"
            f"📈 **Change**: {price_change:.2f} USD ({percent_change:.2f}%)\n"
            f"📉 **Trend**: {trend}\n"
            f"💡 **Recommendation**: {recommendation}\n"
            f"⛔ **Stop Loss**: {stop_loss}\n"
            f"🎯 **Take Profit**: {take_profit}"
        )
        return response
    except Exception as e:
        logging.error(f"Error fetching data for {instrument}: {e}")
        return "❌ Error fetching market data. Try again later."




# ✅ Handle Market Analysis Request
# Handle Market Analysis Request
@dp.callback_query(lambda c: c.data.startswith("analyze_"))
async def analyze_market(callback_query: types.CallbackQuery):
    instrument = callback_query.data.replace("analyze_", "")
    analysis = await get_market_analysis(instrument)

    # ✅ Add "🔄 Start Again" Button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]
        ]
    )

    # Send the analysis result with the button
    await callback_query.message.edit_text(analysis, parse_mode="Markdown", reply_markup=keyboard)




# ✅ Handle AI Signal button
# Handle AI Signal button
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
            [InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]  # ✅ Added Start Again Button
        ]
    )
    await callback_query.message.edit_text("Choose Your Favorite Instruments:", reply_markup=keyboard)


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

# ✅ Handle TradingView AI Signal Alerts
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
                # ✅ Add "Start Again" & "Unsubscribe" Buttons
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🚫 Unsubscribe", callback_data=f"unsubscribe_signal_{user}")],
                        [InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]
                    ]
                )

                # ✅ Send AI Signal Alert with Buttons
                await bot.send_message(chat_id=user, text=message, reply_markup=keyboard)
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
    logging.info(f"🚀 Webhook set: {WEBHOOK_URL}")  # ✅ Fix: Use the variable correctly


# ✅ Remove webhook on shutdown
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logging.info("🛑 Webhook removed")

# ✅ Run FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
