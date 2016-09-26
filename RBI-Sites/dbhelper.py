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

    def get_sites(self, site_name = None):
        query = {}
        if site_name:
            print "Getting sites matching name : " + site_name
            query = {"site.site_group.site_name": site_name}
        return list(self.db.sites.find(query))

    def get_site(self, site_id):
        return self.db.sites.find_one({"_id": site_id})

    def show_site(self, site_id):
        query = {"_id": ObjectId(site_id)}
        return self.db.sites.find(query)

    def find_sites(self, query):
        print "Query : " + str(query)
        return list(self.db.sites.find(query))

    def get_site_count(self,query):
        return self.db.sites.find(query).count()

# The following methods are all to query the output setup collection
    def get_output_count(self):
        return self.db.output.count()

    def get_output_header(self, index):
        query = {"output.header": index}
        return self.db.output.findone(query)

    def get_output_querystr(self, index):
        query = {"output.querystr": index}
        return self.db.output.findone(query)

    def get_output_header_tag(self, index):
        query = {"output.index": index}
        cursor = self.db.output.find_one(query)
        for document in cursor:
            print document
        return document

    def get_output_header_index(self, tag):
        query = {"output.index": tag}
        return self.db.output.findone(query)

    def get_output_header_bytag(self, tag):
        query = {"output.header": tag}
        return self.db.output.findone(query)

    def get_output_querystr_bytag(self, tag):
        query = {"output.querystr": tag}
        return self.db.output.findone(query)


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

    def delete_request(self, request_id):
        self.db.requests.remove({"_id": ObjectId(request_id)})
