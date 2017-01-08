from bson import json_util
import pymongo


client = pymongo.MongoClient()
db = client.freelancer

row = db.projects.find_one({"result.bids": {"$size": 10}})
print json_util.dumps(row)
