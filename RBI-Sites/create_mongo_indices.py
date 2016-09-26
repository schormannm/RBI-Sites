import pymongo

client = pymongo.MongoClient()
c = client['rbi']

print c.users.create_index("email", unique=True)
print c.sites.create_index("site.@instanceID", unique=True)
