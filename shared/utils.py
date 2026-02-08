import requests
from shared.db import get_db
from shared.config import config

bot_logger = config["LOGGER"]["BOT"]
server_logger = config["LOGGER"]["SERVER"]

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

def parse(text) -> str:
    special_chars = r"[]()~`>#+-=|{}.!_"
    return ''.join(['\\' + c if c in special_chars else c for c in str(text)])

def formatter(n: int) -> str:
    if n < 1000:
        return str(n)
    elif 1000 <= n < 1000000:
        return f'{n / 1000:.2f}K'
    else:
        return f'{n / 1000000:.2f}M'

def send_message(chat_id: int, message: str) -> None:
    bot_token = config["BOT_TOKEN"]
    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'MarkdownV2'
            },
            timeout=5
        )
        data = resp.json()

        return data["result"]["message_id"]
    except Exception as e:
        server_logger.error(f"Failed to send message to chat {chat_id}: {e}")

async def permission_check(update, context, groups, owner_command=False, admin_command=False, setup_command=False):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if update.effective_chat.type == "private":
        text = "❌ *This command can only be used in groups\\.*"
        
        await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        return False

    group = groups.find_one({ "ids.group": chat_id })
    if not group and not setup_command:
        text = "⚠️ *Group is not setup for OAuth\\.*\n\n💬 _Use the */setup* command to setup your group for OAuth\\._"
        
        await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        return False

    if admin_command:
        whitelist = group["whitelist"]
        whitelist.append(group["ids"]["owner"])
        if user_id not in whitelist:
            text = "❌ *You are not authorized to use admin commands in this group\\.*"
            await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2") 
            return False

    if owner_command:
        if user_id != group["ids"]["owner"]:
            text = "❌ *Only the group owner is allowed to use this command\\.*"
            await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2") 
            return False
    
    return True

def tweet(chat_id: int, token: str, message=None, tweet_id=0, community_id=0, is_reply=False, is_retweet=False, is_community=False, is_quote=False, user_id=0) -> tuple:
    url = 'https://api.x.com/2/tweets' if not is_retweet else f'https://api.x.com/2/users/{user_id}/retweets'
    if not is_retweet:
        group = groups.find_one({"ids.group": chat_id})
        
        json = {'text': message}

        if not group["settings"]["replies"] and not is_reply:
            json["reply_settings"] = "mentionedUsers"

        if is_reply:
            json["reply"]["in_reply_to_tweet_id"] = tweet_id

        if is_community:
            json["community_id"] = community_id
    else:
        json = {'tweet_id': tweet_id}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    try:
        res = requests.post(url=url, json=json, headers=headers)
        return res, res.json()
    except Exception as e:
        bot_logger.error(f"Failed to send tweet: {e}")

async def handle_successful_tweet(context, chat_id: int, username: str, response: dict, is_reply=False, is_retweet=False, is_quote=False, is_community=False, display=True) -> None:
    tweet_id = response['data']['id'] if not is_retweet else 0
    username = parse(username)
    if not is_retweet:
        text = f"✅ *{'Reply' if is_reply else 'Quote tweet' if is_quote else 'Tweet'} successfully posted by user _||{username}||_\\.*\n" \
            f"🐦 *Tweet ID:* `{tweet_id}`\n" \
            f"🔗 __*[View {'reply' if is_reply else 'tweet'}](https://x\\.com/{username}/status/{tweet_id})*__"
        
        if not is_reply:
            group = groups.find_one({"ids.group": chat_id})
    
            replies_msg = "enabled" if group["settings"]["replies"] else "restricted to mentioned only"
            replies_msg2 = "disable" if group["settings"]["replies"] else "enable"
            text += f"\n\n💬 _Replies for this tweet are {replies_msg}\\. To {replies_msg2} replies for tweets, use the command */set\\_replies*\\._"
    else:
        text = f"✅ *Tweet successfully retweeted by user _{username}_\\.*"
            
    await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2", disable_web_page_preview=True)
    
async def handle_generic_error(context, chat_id: int, res: requests.Response, response: dict) -> None:
    if res.status_code == 403 and 'detail' in response:
        parse_mode = "MarkdownV2"
        if 'duplicate content' in response['detail']:
            text = "❌ *Tweet failed to post\\.*\n" \
                   "⚠️ *Reason:* Duplicate content detected\\. You cannot post the same tweet multiple times\\."
        elif 'deleted' in response['detail'] or 'not visible' in response['detail']:
            text = "❌ *Reply failed to post\\.*\n" \
                   "⚠️ *Reason:* The tweet you attempted to reply to has been deleted or is not visible to you\\."
        else:
            parse_mode = "MarkDown"
            text = f"❌ *Failed to post tweet.*\n" \
                   f"⚠️ *Error code:* {res.status_code}\n" \
                   f"🛑 *Details:* {response.get('detail', 'Unknown error')}"
    else:
        parse_mode = "MarkDown"
        text = f"❌ *Failed to post tweet.*\n" \
               f"⚠️ *Error code:* {res.status_code}\n" \
               f"🛑 *Details:* {response.get('detail', 'Unknown error')}"

    await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
    
async def handle_token_refresh_and_retry(context, chat_id: int, user: dict, refresh_token: str, message=None, tweet_id=0, community_id=0, is_reply=False, is_retweet=False, is_quote=False, is_community=False, display=True, user_id=0) -> None:
    group = groups.find_one({"ids.group": chat_id})
    
    new_access_token = None
    new_refresh_token = None
    
    credentials = user.get("credentials")
    if credentials:
        new_access_token, new_refresh_token = await refresh_oauth_tokens(refresh_token, credentials)

    if not new_access_token:
        for setting in clients:
            TWITTER_CLIENT_ID = setting["client_id"]
            TWITTER_CLIENT_SECRET = setting["client_secret"]
            credentials = base64.b64encode(f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}".encode()).decode('utf-8')

            new_access_token, new_refresh_token = await refresh_oauth_tokens(refresh_token, credentials)

            if new_access_token:
                break

    if not new_access_token:
        groups.update_one(
            {"ids.group": chat_id, "users.username": user["username"]},
            {"$unset": {
                "users.$.access_token": None
            }}
        )
        
        username = parse(user["username"])

        text = f"❌ *User _[{username}](https://x\\.com/{username})_ revoked OAuth access and is no longer valid\\.*"
        return await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        
    groups.update_one(
        {"ids.group": chat_id, "users.username": user["username"]},
        {"$set": {
            "users.$.access_token": new_access_token,
            "users.$.refresh_token": new_refresh_token or refresh_token
        }}
    )

    res, r = tweet(chat_id, new_access_token, message=message, tweet_id=tweet_id, community_id=community_id, is_reply=is_reply, is_retweet=is_retweet, is_quote=is_quote, is_community=is_community, user_id=user_id)
    if res.status_code == 201 or res.status_code == 200:
        if display:
            await handle_successful_tweet(context, chat_id, user["username"], r, is_reply=is_reply, is_retweet=is_retweet, is_quote=is_quote, is_community=is_community)
    else:
        await handle_generic_error(context, chat_id, res, r)
     
async def refresh_oauth_tokens(refresh_token: str, credentials) -> tuple:
    url = 'https://api.twitter.com/2/oauth2/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {'Authorization': f'Basic {credentials}', 'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        res = requests.post(url=url, data=data, headers=headers)
        r = res.json()
        return r.get("access_token"), r.get("refresh_token")
    except Exception as e:
        logger.error(f"Failed to refresh token {refresh_token}: {e}")
        return None, None