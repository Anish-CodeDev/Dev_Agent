import pymongo
from dotenv import load_dotenv
import os
load_dotenv()

client = pymongo.MongoClient(os.getenv('URI'))
db = client[os.getenv('DB_NAME')]
collection = db[os.getenv('COLLECTION_NAME')]

class DBOps:
    def __init__(self):
        self.db = db
        self.collection = collection
    
    def insert_document(self,data):
        try:
            res = self.collection.insert_one(data)
            return res
        except Exception as e:
            return str(e)

    def find_documents(self,query):
        try:
            res = self.collection.find(query)
            return res
        except Exception as e:
            return str(e)
    
    def update_document(self,query,data):
        try:
            res = self.collection.update_one(query,data)
            return res
        except Exception as e:
            return str(e)
    
    def delete_document(self,query):
        try:
            res = self.collection.delete_one(query)
            return res
        except Exception as e:
            return str(e)

    def check_if_agent_exists(self,name):
        try:
            res = self.collection.find_one({'name':name})
            if res:
                return True
            return False
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    db = DBOps()
    res = list(db.find_documents({'name':'flask-backend'}))
    print(res[0]['apps'])