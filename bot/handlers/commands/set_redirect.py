from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def set_redirect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.set_redirect(update, context)

def get_handler():
    return CommandHandler('set_redirect', set_redirect)