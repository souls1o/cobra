from shared.utils import parse
from bot.handlers import keyboards

parse_mode = "MarkdownV2"

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