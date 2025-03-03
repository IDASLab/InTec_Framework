import logging
import datetime
import settings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# Configure Logging
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.test_col = None
        self.connect()

    def connect(self):
        """Establishes a database connection."""
        try:
            logging.info("🔌 Connecting to MongoDB...")
            self.client = MongoClient(settings.DB_URL, serverSelectionTimeoutMS=5000)
            self.db = self.client["edge"]
            self.collection = self.db[settings.DB_COLLECTION]
            self.test_col = self.db["test"]

            # Ping to verify connection
            self.client.admin.command("ping")
            logging.info("✅ Database connected successfully!")
        except ConnectionFailure:
            logging.error("❌ Database connection failed!")
            self.client = None
        except PyMongoError as e:
            logging.error(f"❌ MongoDB error: {e}")
            self.client = None

    def fetch_by_query(self, query, projection):
        """Fetch documents from MongoDB based on a query."""
        if self.collection is None:  # ✅ FIXED HERE
            logging.error("❌ Database not connected. Cannot fetch data.")
            return []
        
        try:
            with self.collection.find(query, projection) as cursor:
                return list(cursor)
        except PyMongoError as e:
            logging.error(f"❌ Error fetching data: {e}")
            return []

    def fetch_data_batch(self, minutes):
        """Fetch only unread (unprocessed) data from MongoDB."""
        query = {
            "processed": False,  # Only fetch unread data
            "date": {"$gte": str(datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes))}
        }
        projection = {"data": 1, "label": 1,"date":1,  "_id": 1}  # Include _id for marking as processed
        return self.fetch_by_query(query, projection)


    def insert(self, data):
        """Insert data into the main collection."""
        if self.collection is None:
            logging.error("❌ Database not connected. Cannot insert data.")
            return
        try:
            self.collection.insert_one(data)
            #logging.info("✅ Data inserted successfully.")
        except PyMongoError as e:
            logging.error(f"❌ Error inserting data: {e}")

    def insert_batch(self, data_list):
        """Insert multiple records into the main collection (batch insert for efficiency)."""
        if self.collection is None:
            logging.error("❌ Database not connected. Cannot insert data.")
            return
        try:
            if data_list:
                self.collection.insert_many(data_list)
                logging.info(f"✅ {len(data_list)} records inserted successfully.")
            else:
                logging.warning("⚠️ No data to insert.")
        except PyMongoError as e:
            logging.error(f"❌ Error inserting batch data: {e}")

    def insert_test(self, data):
        """Insert data into the test collection."""
        if self.test_col is None:
            logging.error("❌ Database not connected. Cannot insert test data.")
            return
        try:
            self.test_col.insert_one(data)
            logging.info("✅ Test data inserted successfully.")
        except PyMongoError as e:
            logging.error(f"❌ Error inserting test data: {e}")

    def insert_test_batch(self, data_list):
        """Insert multiple test records into the test collection (batch insert for efficiency)."""
        if self.test_col is None:
            logging.error("❌ Database not connected. Cannot insert test data.")
            return
        try:
            if data_list:
                self.test_col.insert_many(data_list)
                logging.info(f"✅ {len(data_list)} test records inserted successfully.")
            else:
                logging.warning("⚠️ No test data to insert.")
        except PyMongoError as e:
            logging.error(f"❌ Error inserting batch test data: {e}")

# Create a single instance of the Database class
db = Database()

if __name__ == "__main__":
    db.connect()

