from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def display_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.display_users(update, context)

def get_handler():
    return CommandHandler('display_users', display_users)