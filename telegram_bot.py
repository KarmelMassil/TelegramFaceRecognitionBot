

import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load the .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Define the custom keyboard
keyboard = [['Hello', 'World'], ['Telegram', 'Bot']]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=reply_markup
    )

# Echo the selected button
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ['Hello', 'World', 'Telegram', 'Bot']:
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Please choose a valid button.", reply_markup=reply_markup)

# Main function
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
