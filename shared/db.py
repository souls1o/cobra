from pymongo import MongoClient
from shared.config import config

_client = None
_db = None

def get_db():
    global _client, _db

    if _db is None:
        mongo_uri = config["MONGO_URI"]
        db_name = config["MONGO_DB"]

        _client = MongoClient(
            mongo_uri,
            maxPoolSize=20,
            serverSelectionTimeoutMS=5000,
        )
        _db = _client[db_name]

    return _db
