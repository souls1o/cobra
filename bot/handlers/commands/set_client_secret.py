from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def set_client_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.set_client_secret(update, context)

def get_handler():
    return CommandHandler('set_client_secret', set_client_secret)