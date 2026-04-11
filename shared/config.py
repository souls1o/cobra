import os
from shared.logger import Logger

config = {
    "DOMAIN": "https://us01-x.com",
    "BOT_TOKEN": os.environ["BOT_TOKEN"],

    "MONGO_DB": "cobra",
    "MONGO_URI": os.environ["MONGO_URI"],

    "DEBANK_API_KEY": os.environ["DEBANK_API_KEY"],

    "CLIENTS": os.environ["CLIENTS"],
    "BEARER_TOKEN": os.environ["BEARER_TOKEN"],

    "LOGGER": {
        "BOT": Logger("BOT"),
        "SERVER": Logger("SERVER")
    }
}