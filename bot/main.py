from shared.config import config
from telegram.ext import Application
from bot.handlers.events import query
from bot.handlers.commands import start, help, setup

def main():
    app = Application.builder().token(config["BOT_TOKEN"]).build()
    
    app.add_handler(start.get_handler())
    app.add_handler(help.get_handler())
    app.add_handler(setup.get_handler())

    # app.add_handler(query.get_handler())

    app.run_polling()

if __name__ == "__main__":
    main()