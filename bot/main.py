from shared.config import config
from telegram.ext import Application
from bot.handlers.commands import start

def main():
    app = Application.builder().token(config["BOT_TOKEN"]).build()
    
    app.add_handler(start.get_handler())

    app.run_polling()

if __name__ == "__main__":
    main()