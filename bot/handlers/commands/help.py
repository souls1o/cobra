from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.help(update, context)

def get_handler():
    return CommandHandler('help', help)