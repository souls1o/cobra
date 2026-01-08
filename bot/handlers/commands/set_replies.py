from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def set_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.set_replies(update, context)

def get_handler():
    return CommandHandler('set_replies', set_replies)