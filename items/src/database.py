from pymongo import MongoClient

client = MongoClient(
    host='mongodb://root:example@mongo_items',
    port=27017,
)

db = client.get_database('item')