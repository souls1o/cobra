from bot.handlers import screens
from telegram import CallbackQuery, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    data: str = query.data

    a = data.split(":")
    action = a[0]
    args = a[1:]

    if action == "users":
        await screens.display_users(update, context, args[0], context.user_data["users_message_id"])
    elif action.startswith("whitelist"):

        if action.endswith("add"):
            if not args:
                await screens.add_whitelist(update, context, query)
        else:
            if not args:
                await screens.remove_whitelist(update, context, query)
            else:
                await screens.whitelist_removal(update, context, args[0])

def get_handler():
    return CallbackQueryHandler(query)