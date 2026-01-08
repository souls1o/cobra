from bot.handlers import screens
from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes, MessageHandler, filters

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_whitelist_id"): return

    text = update.message.text.strip()

    if text.isdigit():
        user_id = int(text)

        await screens.whitelist_addition(update, context, user_id)
        
        context.user_data["awaiting_whitelist_id"] = False
    else:
        await context.bot.send_message(update.effective_chat.id, "⚠️ *Value receieved is an invalid user id\\.*", parse_mode="MarkdownV2")
        
def get_handler():
    return MessageHandler(filters.TEXT, message)