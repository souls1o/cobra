from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes, MessageHandler, filters

db = get_db()
groups = db["groups"]

async def migration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg:
        return

    old_id = msg.migrate_from_chat_id
    new_id = msg.migrate_to_chat_id

    if not old_id or not new_id:
        return

    result = db.groups.update_one(
        {"ids.group": old_id},
        {"$set": {"chat_id": new_id, "is_supergroup": True}}
    )

def get_handler():
    return MessageHandler(filters.StatusUpdate.MIGRATE, migration)