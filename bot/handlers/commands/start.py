from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers import screens

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        user_id = update.effective_user.id
        channel_id = "@CobraTool"
        chat_member = await context.bot.get_chat_member(channel_id, user_id)

        is_subscribed = chat_member.status in ['member', 'administrator', 'creator']
        if is_subscribed: await screens.start(update, context)
        else: await screens.unsubscribed(update, context)

        await update.message.delete()

def get_handler():
    return CommandHandler('start', start)