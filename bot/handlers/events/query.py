from bot.handlers import screens
from telegram import CallbackQuery, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    data: str = query.data

    if data.startswith("users"):
        message_id = context.user_data["users_message_id"]
        page = int(data.split(":")[1])

        await screens.display_users(update, context, page, message_id)
    elif data.startswith("whitelist"):
        context.user_data["awaiting_whitelist_id"] = True

        if data.endswith("add"):
            screens.add_whitelist(update, context)
        else:
            screens.remove_whitelist(update, context)

def get_handler():
    return CallbackQueryHandler(query)