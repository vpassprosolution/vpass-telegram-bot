from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify
import asyncio
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7900613582:AAEFQbGO7gk03lHffMNvDRnfWGSbIkH1gQY")

# Flask app for webhook
app = Flask(__name__)

# Dictionary to store subscribed users
subscribed_users = set()

# ✅ Webhook Route to Receive TradingView Alerts
@app.route("/tradingview", methods=["POST"])
def tradingview_webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid request"}), 400

    message = data["message"]
    asyncio.run(send_signal_to_subscribers(message))  # Send signal to Telegram users

    return jsonify({"status": "Message sent to subscribers"}), 200

async def send_signal_to_subscribers(message):
    """Send TradingView alerts to subscribed users."""
    for user in subscribed_users:
        await application.bot.send_message(chat_id=user, text=message)

# ✅ Function to Handle /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    welcome_text = """Welcome to VPASS Pro – Your AI-Powered Trading Companion

At VPASS Pro, we redefine trading excellence through cutting-edge AI technology. Our mission is to empower you with precise, real-time trading signals and actionable insights, enabling you to make informed decisions in dynamic markets.

Whether you're navigating volatile trends or optimizing your portfolio, VPASS Pro is your trusted partner for smarter, data-driven trading.

Explore the future of trading today. Let’s elevate your strategy together.
"""
    # Send Welcome Image
    with open("images/welcome.png", "rb") as image:
        await context.bot.send_photo(chat_id=chat_id, photo=InputFile(image))

    # Send Welcome Text with Button
    keyboard = [[InlineKeyboardButton("🚀 Try VPASS Pro Now", callback_data="show_main_buttons")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup)

# ✅ Function to Show Main Buttons
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

# ✅ AI Signal Feature
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

# ✅ Subscribe User to TradingView Alerts
async def subscribe_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    subscribed_users.add(chat_id)
    await query.answer("Subscribed to Gold Signals!")
    await context.bot.send_message(chat_id=chat_id, text="✅ You have subscribed to Gold Signals. You will receive updates when a new signal is detected.")

# ✅ Unsubscribe User from TradingView Alerts
async def unsubscribe_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        await query.answer("Unsubscribed from Gold Signals!")
        await context.bot.send_message(chat_id=chat_id, text="🚫 You have unsubscribed from Gold Signals. You will no longer receive updates.")
    else:
        await query.answer("You are not subscribed!")

# ✅ Initialize Telegram Bot
application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(show_main_buttons, pattern="show_main_buttons"))
application.add_handler(CallbackQueryHandler(ai_signal, pattern="ai_signal"))
application.add_handler(CallbackQueryHandler(subscribe_signal, pattern="subscribe_signal"))
application.add_handler(CallbackQueryHandler(unsubscribe_signal, pattern="unsubscribe_signal"))

# ✅ Run Flask Webhook
def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ✅ Run Both Telegram Bot & Flask Webhook
async def main():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    run_flask()

if __name__ == "__main__":
    asyncio.run(main())
