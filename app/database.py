from pymongo import MongoClient
import datetime


class Database:
    def __init__(self, credentials):
        self.client = MongoClient(credentials['ip'], credentials['port'])
        self.db = self.client[credentials['database']]
        self.collection = self.db[credentials['collection']]

    def find_one(self, query):
        return self.collection.find_one(query)

    def find(self, query):
        return self.collection.find(query)

    def insert_image(self, query):
        date = datetime.datetime.now()
        date = date.strftime("%Y-%m-%d %H:%M")

        return self.collection.insert_one({
            'author': query['author'],
            'name': query['name'],
            'date': date
        })
