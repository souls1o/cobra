from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def delete_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.delete_tweet(update, context)

def get_handler():
    return CommandHandler('delete_tweet', delete_tweet)