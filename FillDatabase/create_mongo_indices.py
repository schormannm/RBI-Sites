import pymongo

client = pymongo.MongoClient()
c = client['rbi']

print c.sites.create_index("site.@instanceID", unique=True)
