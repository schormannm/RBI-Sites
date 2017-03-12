import pymongo
from bson import ObjectId
import datetime

DATABASE = "rbi"


class DBHelper:

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client[DATABASE]

    def number_of_records(self):
        return self.db.sites.count()

    def check_existing_site(self, site, site_id):
        print "Checking existence of " + site_id + " in database"
        result = self.db.sites.find_one({"site.@instanceID": site_id})
        if result is not None:
            return True
        else:
            return False

    def update_site_paths(self, site_id, full_filename):
        file_path = ""
        file_name = ""
        mog_file_name = full_filename
        meta_update = {
            "site.meta.file_path": file_path,
            "site.meta.file_name": file_name,
            "site.meta.mog_file_name": mog_file_name
        }
        _id = self.get_site_byUUID(site_id)
        self.db.sites.update({"_id": ObjectId(_id)}, {"$set": meta_update})

    def add_site(self, site, site_id):
        try:
            self.db.sites.insert_one({"site": site})
            # print "Matched: " + str(result.matched_count) + "   Modified: " + str(result.modified_count)
            print "Site ID: " + site_id + " added to database"
            return True
        except pymongo.errors.DuplicateKeyError:
            print "Duplicate key error exception triggered - probable duplicate"
        return False

    def get_user(self, email):
        return self.db.users.find_one({"email": email})

    def add_user(self, email, salt, hashed):
        self.db.users.insert({"email": email, "salt": salt, "hashed": hashed})

    def get_site_byUUID(self, site_id):
        return self.db.sites.find_one({"site.@instanceID": site_id})

    def get_site_byID(self, _id):
        query = {"_id": ObjectId(_id)}
        return self.db.sites.find(query)

    def get_meta_file_path(self, site_id):
        site = self.db.sites.find_one({"site.@instanceID": site_id})
        path = site["meta"]["file_path"]
        return path
