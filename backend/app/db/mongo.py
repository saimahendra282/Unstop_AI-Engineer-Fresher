from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from ..config import get_settings
from functools import lru_cache

@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    client = MongoClient(settings.mongo_uri)
    return client

def get_db():
    settings = get_settings()
    return get_client()[settings.mongo_db]

def emails_col() -> Collection:
    col = get_db()["emails"]
    col.create_index([("message_id", ASCENDING)], unique=True)
    col.create_index([("priority_score", ASCENDING)])
    col.create_index([("received_at", ASCENDING)])
    return col

def responses_col() -> Collection:
    return get_db()["responses"]

def kb_col() -> Collection:
    return get_db()["knowledge_chunks"]
