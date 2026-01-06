from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def post_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await screens.post_tweet(update, context)

def get_handler():
    return CommandHandler('post_tweet', post_tweet)