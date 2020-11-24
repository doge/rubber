from pymongo import MongoClient
import datetime


class Database:
    def __init__(self, credentials, collection):
        # use this on production server
        self.client = MongoClient('mongodb://%s:%s@%s:%s' % (credentials['user'], credentials['password'],
                                                             credentials['ip'], credentials['port']))
        # use this on local server
        # self.client = MongoClient(credentials['ip'], credentials['port'])
        self.db = self.client[credentials['db_name']]
        self.collection = self.db[collection]

    def find_one(self, query):
        return self.collection.find_one(query)

    def find(self, query=None):
        return self.collection.find(query)

    def insert(self, query):
        self.collection.insert_one(query)

    def image_exists(self, query):
        if self.collection.find_one(query):
            return True
        return False

    def insert_image(self, query):
        date = datetime.datetime.now()
        date = date.strftime("%Y-%m-%d %H:%M")

        return self.collection.insert_one({
            'author': query['author'],
            'name': query['name'],
            'date': date
        })

    def get_data(self, username):
        return self.collection.find({
            'author': username
        })

    def delete_one(self, query):
        return self.collection.delete_one(query)

    def update_one(self, query, new_values):
        return self.collection.update_one(query, new_values)
