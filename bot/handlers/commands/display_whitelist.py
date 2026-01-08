from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def display_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.display_whitelist(update, context)

def get_handler():
    return CommandHandler('display_whitelist', display_whitelist)