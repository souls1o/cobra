import os
from shared.logger import Logger
from dotenv import load_dotenv
load_dotenv()

config = {
    "DOMAIN": "https://us01-x.com",
    "BOT_TOKEN": os.environ["BOT_TOKEN"],

    "MONGO_DB": "cobra",
    "MONGO_URI": os.environ["MONGO_URI"],

    "DEBANK_API_KEY": os.environ["DEBANK_API_KEY"],

    "CLIENTS": os.environ["CLIENTS"],

    "LOGGER": {
        "BOT": Logger("BOT"),
        "SERVER": Logger("SERVER")
    }
}