from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.check_balance(update, context)

def get_handler():
    return CommandHandler('check_balance', check_balance)