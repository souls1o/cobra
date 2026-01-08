from shared.db import get_db
from shared.config import config
from telegram.ext import Application
from bot.handlers.events import query, message
from bot.handlers.commands import start, help, setup, post_tweet, delete_tweet, display_users, display_endpoint, display_whitelist, set_client_id, set_client_secret, set_redirect, set_spoof, set_replies, check_auth

def main():
    app = Application.builder().token(config["BOT_TOKEN"]).build()
    
    app.add_handler(start.get_handler())
    app.add_handler(help.get_handler())
    app.add_handler(setup.get_handler())
    app.add_handler(post_tweet.get_handler())
    app.add_handler(delete_tweet.get_handler())
    app.add_handler(display_users.get_handler())
    app.add_handler(display_endpoint.get_handler())
    app.add_handler(display_whitelist.get_handler())
    app.add_handler(set_client_id.get_handler())
    app.add_handler(set_client_secret.get_handler())
    app.add_handler(set_redirect.get_handler())
    app.add_handler(set_spoof.get_handler())
    app.add_handler(set_replies.get_handler())
    app.add_handler(check_auth.get_handler())

    app.add_handler(query.get_handler())
    app.add_handler(message.get_handler())

    app.run_polling()

if __name__ == "__main__":
    main()