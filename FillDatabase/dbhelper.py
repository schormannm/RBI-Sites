import pymongo
from bson import ObjectId

DATABASE = "rbi"


class DBHelper:

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client[DATABASE]

    def number_of_records(self):
        return self.db.sites.count()

    def add_site(self, site):
        site_id = site["@instanceID"]  # site data comes in as a dictionary, so we can search for records based on it
        print site_id
        result = self.db.sites.find_one({"site.@instanceID": site_id})
        if result is not None:
            print "Found a match  in db"
            return True
        else:
            try:
                self.db.sites.insert_one({"site": site})
                # print "Matched: " + str(result.matched_count) + "   Modified: " + str(result.modified_count)
                print "Site with ID: " + site_id + " added to database"
                return True
            except pymongo.errors.DuplicateKeyError:
                print "Duplicate key error exception triggered"
                return False

    def get_user(self, email):
        return self.db.users.find_one({"email": email})

    def add_user(self, email, salt, hashed):
        self.db.users.insert({"email": email, "salt": salt, "hashed": hashed})

    def add_table(self, number, owner):
        new_id = self.db.tables.insert({"number": number, "owner": owner})
        return new_id

    def update_table(self, _id, url):
        self.db.tables.update({"_id": _id}, {"$set": {"url": url}})

    def get_tables(self, owner_id):
        return list(self.db.tables.find({"owner": owner_id}))

    def get_table(self, table_id):
        return self.db.tables.find_one({"_id": ObjectId(table_id)})

    def delete_table(self, table_id):
        self.db.tables.remove({"_id": ObjectId(table_id)})

    def add_request(self, table_id, time):
        table = self.get_table(table_id)
        try:
            self.db.requests.insert({"owner": table['owner'], "table_number": table[
                                    'number'], "table_id": table_id, "time": time})
            return True
        except pymongo.errors.DuplicateKeyError:
            return False

    def get_requests(self, owner_id):
        return list(self.db.requests.find({"owner": owner_id}))

    def delete_request(self, request_id):
        self.db.requests.remove({"_id": ObjectId(request_id)})
