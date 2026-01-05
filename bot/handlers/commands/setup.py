from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.setup(update, context)

def get_handler():
    return CommandHandler('setup', setup)