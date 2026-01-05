from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def unsubscribed():
    keyboard = [
        [InlineKeyboardButton("🔗 Channel", url="https://t.me/+GSi9ZXRMgMo5MzRh")]
    ]
    return InlineKeyboardMarkup(keyboard)

def add_to_group():
    keyboard = [
        [InlineKeyboardButton("➕ Add to group", url="https://t.me/CobraLoggerBot?startgroup=start")]
    ]
    return InlineKeyboardMarkup(keyboard)