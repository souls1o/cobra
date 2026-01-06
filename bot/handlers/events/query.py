from bot.handlers import screens
from telegram import CallbackQuery, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    data: str = query.data

    if data.startswith("users_page"):
        message_id = context.user_data["message_id"]
        page = int(data.split(":")[1])

        await screens.display_users(update, context, page, message_id)

def get_handler():
    return CallbackQueryHandler(query)