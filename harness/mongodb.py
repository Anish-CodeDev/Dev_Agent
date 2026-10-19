import pymongo
from functools import lru_cache

from google_api import get_environment_setting


@lru_cache(maxsize=4)
def _database_resources(uri: str, db_name: str, collection_name: str):
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    return client, db, db[collection_name]

class DBOps:
    def _resources(self):
        uri = get_environment_setting("URI")
        db_name = get_environment_setting("DB_NAME")
        collection_name = get_environment_setting("COLLECTION_NAME")
        if not uri or not db_name or not collection_name:
            raise RuntimeError(
                "MongoDB settings are incomplete. Configure URI, DB_NAME, and COLLECTION_NAME."
            )
        return _database_resources(uri, db_name, collection_name)

    @property
    def db(self):
        return self._resources()[1]

    @property
    def collection(self):
        return self._resources()[2]
    
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