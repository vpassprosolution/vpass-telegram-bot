from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import os
from flask import Flask, request
import threading

# Get bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7900613582:AAEFQbGO7gk03lHffMNvDRnfWGSbIkH1gQY")

# Webhook URL from Railway
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://vpass-telegram-bot-production.up.railway.app")

# Get Port from Railway environment (Default 8080 if not found)
PORT = int(os.getenv("PORT", 8080))

# Flask app for handling webhook requests
app = Flask(__name__)

# Dictionary to store subscribed users
subscribed_users = set()

# Initialize Telegram bot application
application = Application.builder().token(TOKEN).build()

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)  # ✅ Proper async handling
    return "OK", 200

# Function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    welcome_text = """Welcome to VPASS Pro – Your AI-Powered Trading Companion

At VPASS Pro, we redefine trading excellence through cutting-edge AI technology. Our mission is to empower you with precise, real-time trading signals and actionable insights, enabling you to make informed decisions in dynamic markets.

Whether you're navigating volatile trends or optimizing your portfolio, VPASS Pro is your trusted partner for smarter, data-driven trading.

Explore the future of trading today. Let’s elevate your strategy together.
"""
    with open("images/welcome.png", "rb") as image:
        await context.bot.send_photo(chat_id=chat_id, photo=InputFile(image))

    keyboard = [[InlineKeyboardButton("🚀 Try VPASS Pro Now", callback_data="show_main_buttons")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup)

async def show_main_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📈 AI Trade", callback_data="ai_trade"),
         InlineKeyboardButton("📊 AI Signal", callback_data="ai_signal")],
        [InlineKeyboardButton("🔍 Deepseek", callback_data="deepseek"),
         InlineKeyboardButton("🤖 ChatGPT", callback_data="chatgpt")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Access Your Exclusive Trading Tools:", reply_markup=reply_markup)

# AI Signal Feature
async def ai_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📩 Get Gold Signal", callback_data="subscribe_signal")],
        [InlineKeyboardButton("🚫 Unsubscribe Signal", callback_data="unsubscribe_signal")],
        [InlineKeyboardButton("🔙 Back", callback_data="show_main_buttons")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="AI Signal Options:", reply_markup=reply_markup)

async def subscribe_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    subscribed_users.add(chat_id)
    await query.answer("Subscribed to Gold Signals!")
    await context.bot.send_message(chat_id=chat_id, text="✅ You have subscribed to Gold Signals. You will receive updates when a new signal is detected.")

async def unsubscribe_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        await query.answer("Unsubscribed from Gold Signals!")
        await context.bot.send_message(chat_id=chat_id, text="🚫 You have unsubscribed from Gold Signals. You will no longer receive updates.")
    else:
        await query.answer("You are not subscribed!")

async def tradingview_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    for user in subscribed_users:
        await context.bot.send_message(chat_id=user, text=message)

# Placeholder functions
async def ai_trade(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer("AI Trade feature coming soon!")
async def deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer("Deepseek feature coming soon!")
async def chatgpt(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.callback_query.answer("ChatGPT feature coming soon!")

# Add Handlers to the Bot
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(show_main_buttons, pattern="show_main_buttons"))
application.add_handler(CallbackQueryHandler(ai_trade, pattern="ai_trade"))
application.add_handler(CallbackQueryHandler(ai_signal, pattern="ai_signal"))
application.add_handler(CallbackQueryHandler(subscribe_signal, pattern="subscribe_signal"))
application.add_handler(CallbackQueryHandler(unsubscribe_signal, pattern="unsubscribe_signal"))
application.add_handler(CallbackQueryHandler(deepseek, pattern="deepseek"))
application.add_handler(CallbackQueryHandler(chatgpt, pattern="chatgpt"))
application.add_handler(CommandHandler("tradingview", tradingview_alert))

# Set Webhook
async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

def run_flask():
    """Runs Flask in a separate thread to avoid blocking."""
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

async def main():
    """Initialize and start the bot properly."""
    await application.initialize()  # ✅ Proper async initialization
    await application.start()  # ✅ Ensure bot is running
    await set_webhook()  # ✅ Set webhook

    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Keep the bot running
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())  # ✅ Use asyncio.run() to execute the main async function
