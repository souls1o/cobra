from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def unsubscribed():
    keyboard = [
        [InlineKeyboardButton("🔗 Channel", url="https://t.me/+1diht9yrwwc0YWM5")]
    ]
    return InlineKeyboardMarkup(keyboard)

def add_to_group():
    keyboard = [
        [InlineKeyboardButton("➕ Add to group", url="https://t.me/CobraTool?startgroup=start")]
    ]
    return InlineKeyboardMarkup(keyboard)