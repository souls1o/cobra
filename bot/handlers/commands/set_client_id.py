from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def set_client_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.set_client_id(update, context)

def get_handler():
    return CommandHandler('set_client_id', set_client_id)