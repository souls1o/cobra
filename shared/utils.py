import requests
from shared.config import config

bot_logger = config["LOGGER"]["BOT"]
server_logger = config["LOGGER"]["SERVER"]

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

async def permission_check(update, groups, admin_command=False):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if update.effective_chat.type == "private":
        text = "❌ *This command can only be used in groups\\.*"
        
        await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        return False

    group = groups.find_one({ "group.id": chat_id })
    if not group:
        text = "⚠️ *Group is not setup for OAuth\\.*\n\n💬 _Use the */setup* command to setup your group for OAuth\\._"
        
        await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        return False

    if admin_command == True:
        whitelist = group["whitelist"]
        if user_id not in whitelist and user_id != group["owner_id"]:
            text = "❌ *You are not authorized to use admin commands in this group\\.*"
            await context.bot.send_message(chat_id, text, parse_mode="MarkdownV2") 
            return False
    
    return True