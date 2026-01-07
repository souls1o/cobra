from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.check_auth(update, context)

def get_handler():
    return CommandHandler('check_auth', check_auth)