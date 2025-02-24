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




# ✅ Load bot token from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your .env file.")# ✅ Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ✅ Define Webhook URL - Ensure it's the correct Railway bot service URL
WEBHOOK_URL = "https://web-production-ceec.up.railway.app/webhook"


# ✅ Setup logging for debugging
logging.basicConfig(level=logging.INFO)


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


# ✅ Handle "Try VPASS Pro Now" button
@dp.callback_query(lambda c: c.data == "show_main_buttons")
async def show_main_buttons(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 VPASS SMART SIGNAL", callback_data="ai_signal")],
            [InlineKeyboardButton(text="📉 VPASS AI SENTIMENTS", callback_data="ai_sentiment")],  
            [InlineKeyboardButton(text="🤖 AI AGENT INSTANTS SIGNAL", callback_data="ai_super_agent")],  
            
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
            [InlineKeyboardButton(text="🔙 Back", callback_data="show_main_buttons")]  # ✅ Added Start Again Button
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


# ✅ Handle AI Super Agent Button Click
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


@dp.callback_query(lambda c: c.data.startswith("sentiment_"))
async def fetch_sentiment(callback_query: types.CallbackQuery):
    instrument = callback_query.data.replace("sentiment_", "")
    sentiment_report = await get_sentiment(instrument)

    # ✅ Add "🔄 Start Again" Button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Start Again", callback_data="ai_sentiment")]
        ]
    )

    await callback_query.message.edit_text(sentiment_report, parse_mode="Markdown", reply_markup=keyboard)


# ✅ Dictionary to store user messages
user_messages = {}

# ✅ Handle AI Super Agent Button Click
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
            [InlineKeyboardButton(text="🔄 Start Again", callback_data="start_again_main")]
        ]
    )

    await asyncio.sleep(2)  # ✅ Wait 2 seconds for a smooth effect

    # ✅ Step 4: Delete "Fetching AI Recommendation..." message
    try:
        await bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
    except Exception:
        pass  # Ignore error if already deleted

    # ✅ Step 5: Send the AI recommendation message
    sent_message = await bot.send_message(chat_id=chat_id, text=ai_signal_message, parse_mode="Markdown", reply_markup=keyboard)

    # ✅ Step 6: Store all messages in a list for this user
    if chat_id not in user_messages:
        user_messages[chat_id] = []
    
    # Store message IDs
    user_messages[chat_id].append(sent_message.message_id)


# ✅ Handle "Start Again" Button: Delete ALL Previous Messages
@dp.callback_query(lambda c: c.data == "start_again_main")
async def start_again_main(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id

    # ✅ Step 1: Delete **ALL previous messages** stored for this user
    if chat_id in user_messages:
        for message_id in user_messages[chat_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception:
                pass  # Ignore errors if message is already deleted

        # ✅ Clear message history after deleting
        user_messages[chat_id] = []

    # ✅ Step 2: Show Main Buttons Again
    await show_main_buttons(callback_query)








# ✅ VPASS AI SENTIMENT API URL (Use your actual Railway URL)
VPASS_AI_SENTIMENT_URL = "https://sentiment-data-centre-production.up.railway.app/sentiment/"

# ✅ Function to fetch sentiment analysis from VPASS AI SENTIMENT
async def get_sentiment(instrument):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VPASS_AI_SENTIMENT_URL}{instrument}")
            if response.status_code == 200:
                return response.json()["sentiment_analysis"]
            else:
                return "⚠️ Failed to fetch sentiment analysis. Try again later."
    except Exception as e:
        return f"⚠️ Error fetching sentiment data: {str(e)}"

# ✅ Handle /sentiment command in the bot
@dp.message(Command("sentiment"))
async def sentiment_command(message: types.Message):
    instrument = message.text.replace("/sentiment", "").strip().upper()

    if instrument in ["XAUUSD", "BTC", "ETH", "DJI", "IXIC", "EURUSD", "GBPUSD"]:
        sentiment_report = await get_sentiment(instrument)

        # Add a "🔄 Start Again" button
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]]
        )

        await message.reply(sentiment_report, reply_markup=keyboard)
    else:
        await message.reply("⚠️ Invalid instrument. Use one of: XAUUSD, BTC, ETH, DJI, IXIC, EURUSD, GBPUSD.")


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



# ✅ Handle ai sentiment button
@dp.callback_query(lambda c: c.data == "ai_sentiment")
async def ai_sentiment_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥇 Gold", callback_data="sentiment_XAUUSD")],
            [
                InlineKeyboardButton(text="₿ Bitcoin", callback_data="sentiment_BTC"),
                InlineKeyboardButton(text="💎 Ethereum", callback_data="sentiment_ETH")
            ],
            [
                InlineKeyboardButton(text="📊 Dow Jones", callback_data="sentiment_DJI"),
                InlineKeyboardButton(text="📈 Nasdaq", callback_data="sentiment_IXIC")
            ],
            [
                InlineKeyboardButton(text="💹 EUR/USD", callback_data="sentiment_EURUSD"),
                InlineKeyboardButton(text="💷 GBP/USD", callback_data="sentiment_GBPUSD")
            ],
            [InlineKeyboardButton(text="🔙 Back", callback_data="show_main_buttons")]
        ]
    )
    await callback_query.message.edit_text("📉 Choose an instrument for sentiment analysis:", reply_markup=keyboard)



# ✅ Webhook for Telegram Updates
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    update_obj = types.Update(**update)
    await dp.feed_update(bot, update_obj)
    return {"status": "ok"}


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
