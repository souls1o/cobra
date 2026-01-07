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

def refresh():
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_endpoint")]
    ]
    return InlineKeyboardMarkup(keyboard)

def users_pagination(users, page, total_pages, per_page):
    keyboard = []
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("« Start", callback_data=f"users:1"))
        nav_buttons.append(InlineKeyboardButton("‹ Prev", callback_data=f"users:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="none"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ›", callback_data=f"users:{page+1}"))
        nav_buttons.append(InlineKeyboardButton("End »", callback_data=f"users:{total_pages}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard)

def whitelist():
    keyboard = [
        [InlineKeyboardButton("➕ Add to whitelist", callback_data="whitelist_add")],
        [InlineKeyboardButton("➖ Remove from whitelist", callback_data="whitelist_remove")]
    ]
    return InlineKeyboardMarkup(keyboard)