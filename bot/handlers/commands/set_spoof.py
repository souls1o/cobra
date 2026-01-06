from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def set_spoof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.set_spoof(update, context)

def get_handler():
    return CommandHandler('set_spoof', set_spoof)