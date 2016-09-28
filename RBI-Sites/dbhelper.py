import pymongo
from bson import ObjectId

DATABASE = "rbi"


class DBHelper:

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client[DATABASE]

# user methods
    def get_user(self, email):
        return self.db.users.find_one({"email": email})

    def add_user(self, email, salt, hashed):
        self.db.users.insert({"email": email, "salt": salt, "hashed": hashed})

# site manipulation methods
    def add_site(self, site):           # taken from the FillDatabase project
        try:
            self.db.sites.insert({"site": site})
            return True
        except pymongo.errors.DuplicateKeyError:
            return False

    def update_site(self, _id, url):
        self.db.sites.update({"_id": _id}, {"$set": {"url": url}})

    def update_site_manual(self, _id, manual):
        # manual = {"site.manual.updated": "Yes", "site.manual.site_classification": "K"}
        # manual = {
        #     'site.manual.updated': 'True',
        #     'site.manual.site_classification': "J",
        #     'site.manual.site_release_date': "",
        #     'site.manual.as_built_available': "",
        #     'site.manual.fault_description': "",
        #     'site.manual.mast_engineer': "Mark",
        #     'site.manual.mast_upgraded': "",
        #     'site.manual.mast_upgraded_date': "",
        #     'site.manual.capacity_top': "",
        #     'site.manual.capacity_10_from_top': "",
        #     'site.manual.update_date': ""
        # }

        print manual
        self.db.sites.update({"_id": ObjectId(_id)}, {"$set": manual})


    def check_manual_exists(self, _id):
        result = len(list(self.db.sites.find({"_id": ObjectId(_id), "site.manual.updated": "True"})))
        print result
        if result:
            return True
        else:
            return False

    def get_sites(self, site_name = None):
        query = {}
        if site_name:
            print "Getting sites matching name : " + site_name
            query = {"site.site_group.site_name": site_name}
        return list(self.db.sites.find(query))

    def get_site(self, site_id):
        return self.db.sites.find_one({"_id": site_id})

    def show_site(self, _id):
        query = {"_id": ObjectId(_id)}
        return self.db.sites.find(query)

    def find_sites(self, query):
        print "Query : " + str(query)
        return list(self.db.sites.find(query))

    def get_site_count(self,query):
        return self.db.sites.find(query).count()

    def delete_site(self, site_id):
        self.db.sites.remove({"_id": ObjectId(site_id)})


# old methods from the waiter project
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

