from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def display_endpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.display_endpoint(update, context)

def get_handler():
    return CommandHandler('display_endpoint', display_endpoint)