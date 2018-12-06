import pymongo
from datetime import datetime
import geo

class Db():

	def __init__(self, conn="mongodb://localhost:27017/", dbName="asint"):
		self.client = pymongo.MongoClient(conn)
		self.db = self.client[dbName]
	
	#________________________________________________________________________
	#### Users ####
	def insertUser(self, istID, location, myRange):
		try:
			self.db["users"].insert_one({"_id": istID, "location": location, "range": myRange})
			return True
		except:
			print("Error inserting user")
			return False

	def removeUser(self, istID):
		try:
			self.db["users"].delete_one({"_id": istID})
			return True
		except:
			print("Error removing user")
			return False

	def updateUserLocation(self, istID, lat, lon):
		try:
			self.db["users"].update_one({"_id": istID}, {"$set": {"location": location}})
			return True
		except:
			print("Error changing user location")
			return False

	def updateUserRange(self, newRange):
		try:
			self.db["users"].update_one({"_id": istID}, {"$set": {"range": myRange}})
			return True
		except:
			print("Error changing user range")
			return False

	def getAllLoggedUsers(self):
		return self.db["users"].find()

	def getUsersInRange(self, istid):
		u = self.db["users"].find_one({'_id':istid})

		inRange = lambda u1,u2: geo.distance(u1["location"],u2["location"]) < u1["range"]

		allusers = self.db["users"].find()
		return [user['_id'] for user in allusers if user['_id'] != istid and inRange(user, u)]


	#________________________________________________________________________
	#### Movements ####
	def insertMovement(self, user, location, buildingID):
		try:
			self.db["movements"].insert_one({"user":user, "location":location, "building": buildingID, "time": datetime.now()})
			return True
		except:
			print("Error inserting movement")
			return False

	def getUserMovements(self, user):
		return self.db["movements"].find({"_id": user})

	def getBuildingMovements(self, buildingID):
		return self.db["movements"].find({"building": buildingID})

	#________________________________________________________________________
	#### Messages ####
	def insertMessage(self, src, dest, msg, location, buildingID):
		try:
			self.db["messages"].insert_one({"src": src, "dst": dst, "content": msg, "location": location, "building": buildingID ,"time": datetime.now()})
			return True
		except:
			print("Error inserting message")
			return False

	def getUserMessages(self, user):
		try:
			self.db["messages"].find({"_id": user}, {"dest": 0}) #excludes destiny from the result
			return True
		except:
			print("Error getting messages")
			return False

	def getAllMessages(self):
		return self.db["messages"].find()

	def getBuildingMessages(self, buildingID):
		return self.db["messages"].find({"building": buildingID})
	#________________________________________________________________________
	#### Buildings ####
	def insertBuildings(self, buildingsList):
		try:
			self.db["buildings"].insert_many(buildingsList)
			return True
		except:
			print("Error inserting movement")
			return False
	#________________________________________________________________________
	#### Bots ####
	def insertBot(self, id):
		try:
			return db["bots"].insert_one({'building':id}).inserted_id.binary
		except:
			print('Error inserting Bot')
			return False

	def deleteBot(self, k):
		try:
			db["bots"].delete_one({'key':k})
			return True
		except:
			return False








