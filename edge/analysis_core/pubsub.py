import time
import json
import threading
import logging
import paho.mqtt.client as mqtt
import settings
import inference
import reduction
import outlier
from dbmodel import db  # Import Database instance
from datetime import datetime

client_subscriber = mqtt.Client(f"{settings.CLIENT_ID}_Subscriber")
client_publisher = mqtt.Client(f"{settings.CLIENT_ID}_Publisher")

active_sensors = set()

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Initialize MQTT clients
client_subscriber = mqtt.Client(f"{settings.CLIENT_ID}_Subscriber")
client_publisher = mqtt.Client(f"{settings.CLIENT_ID}_Publisher")

# ✅ Subscriber: On Connect
def on_connect_subscriber(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"✅ Subscribed to {settings.SENSOR_MQTT_BROKER}:{settings.SENSOR_MQTT_PORT} [{settings.SENSOR_MQTT_TOPIC}]")
        client.subscribe(settings.SENSOR_MQTT_TOPIC)
    else:
        logging.error(f"❌ Subscription failed with code {rc}. Retrying...")

# 📩 Subscriber: On Message (Data Processing Pipeline)
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode()
        #logging.info(f"📩 [RECEIVED] Data received on topic: {settings.SENSOR_MQTT_TOPIC}")

        # Convert to JSON if possible
        data = json.loads(payload) if payload.startswith("{") else {"raw_data": payload}

        if not data:
            logging.warning("⚠️ Received empty message. Skipping processing.")
            return

        # Detect new sensor
        sensor_name = data.get("device", "Unknown_Sensor")  # Ensure a sensor identifier is present
        if sensor_name not in active_sensors:
            active_sensors.add(sensor_name)
            logging.info(f"🆕 [NEW SENSOR] Sensor {sensor_name} started publishing data.")

        # Step 1: Pass Data to Inference Module
        #logging.info("🧠 Sending data to inference module...")
        inference.feed(data)

        # Step 2: Pass Processed Data to Outlier Detection Module
        #logging.info("🔍 Sending data to outlier detection module...")
        outlier.feed(data)

        # Step 3: Store Processed Data in MongoDB
        
        db.insert(data)
        #logging.info("🛢️ [STORED] Data successfully saved to MongoDB.")

    except Exception as e:
        logging.error(f"❌ [ERROR] Failed to process incoming message: {e}", exc_info=True)

# ✅ Publisher: On Connect
def on_connect_publisher(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"✅ Publisher connected to {settings.CLOUD_MQTT_BROKER}:{settings.CLOUD_MQTT_PORT} [{settings.CLOUD_MQTT_TOPIC}]")
    else:
        logging.error(f"❌ Publisher connection failed with code {rc}. Retrying...")

# 🔄 Handles disconnection and reconnection attempts
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning(f"⚠️ [DISCONNECTED] {client._client_id.decode()} - Attempting to reconnect...")
        reconnect_client(client)

# 🔄 Reconnection Function with Backoff
def reconnect_client(client):
    attempt = 1
    while True:
        try:
            if "Subscriber" in client._client_id.decode():
                client.connect(settings.SENSOR_MQTT_BROKER, settings.SENSOR_MQTT_PORT, 60)
            else:
                client.connect(settings.CLOUD_MQTT_BROKER, settings.CLOUD_MQTT_PORT, 60)
            logging.info(f"🔄 [RECONNECTED] {client._client_id.decode()}")
            break
        except Exception as e:
            wait_time = min(5 * attempt, 60)  # Increase wait time up to 60s
            logging.error(f"❌ [ERROR] Reconnection failed (Attempt {attempt}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            attempt += 1

# ⏳ Periodic Data Fetching & Publishing
# ✅ Fetch unread data, process it, and publish to cloud
def fetch_reduce_and_publish():
    while True:
        try:
            time.sleep(settings.CLOUD_SYNC_PERIOD * 60)  # Convert minutes to seconds
            
            logging.info("🔍 Fetching unread data from DB for training...")
            data_batch = db.fetch_data_batch(settings.CLOUD_SYNC_PERIOD)
             # ✅ Convert ObjectId to string for readability
            if not data_batch:
                logging.info("📭 No unread data found. Skipping training data publication.")
                continue

            processed_batch = []
            processed_ids = []  # Track processed document IDs

            # Extract time range
            timestamps = [data.get("date") for data in data_batch if "date" in data]
            first_date = min(timestamps) if timestamps else "N/A"
            last_date = max(timestamps) if timestamps else "N/A"

            for data in data_batch:
                if "data" not in data:
                    logging.warning("⚠️ Skipping entry: Missing 'data' field.")
                    continue

                # Reduce Data using Dimensionality Reduction
                reduced_data = reduction.reduce_data(data["data"])
                if reduced_data:
                    try:
                        red_json_data = json.loads(reduced_data)
                        red_json_data["label"] = int(data.get("label", -1))  # Add label if available
                        processed_batch.append(red_json_data)
                        processed_ids.append(data["_id"])  # Store document ID for marking as read
                    except json.JSONDecodeError as e:
                        logging.error(f"❌ Error converting reduced data to JSON: {e}")
                        continue

            if processed_batch:
                msg = json.dumps({"edge_id": settings.CLIENT_ID, "data": processed_batch})
                client_publisher.publish(settings.TRAINING_MQTT_TOPIC, msg)
                logging.info(f"📤 Published {len(processed_batch)} records from {first_date} to {last_date} to {settings.TRAINING_MQTT_TOPIC}")


                # ✅ Mark Data as Read in MongoDB
                db.collection.update_many({"_id": {"$in": processed_ids}}, {"$set": {"processed": True}})
                #logging.info("✅ Marked published data as processed.")

        except Exception as e:
            logging.error(f"❌ [ERROR] Failed during reduction and publishing: {e}", exc_info=True)


# 🔗 Assign MQTT Callbacks
client_subscriber.on_connect = on_connect_subscriber
client_subscriber.on_message = on_message
client_subscriber.on_disconnect = on_disconnect

client_publisher.on_connect = on_connect_publisher
client_publisher.on_disconnect = on_disconnect

# 🔌 Initial Connection with Retry Logic
def connect_with_retry(client, broker, port):
    attempt = 1
    while True:
        try:
            logging.info(f"🔌 [CONNECTING] {client._client_id.decode()} to {broker}:{port}...")
            client.connect(broker, port, 60)
            logging.info(f"✅ [CONNECTED] {client._client_id.decode()} to {broker}:{port}")
            break
        except Exception as e:
            wait_time = min(5 * attempt, 60)
            logging.error(f"❌ [ERROR] Connection failed (Attempt {attempt}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            attempt += 1

# 🚀 Start the MQTT Forwarder (Runnable from Main)
def run():
    logging.info("🚀 Starting MQTT Forwarder Module...")

    # Connect to Brokers with Retry Logic
    connect_with_retry(client_subscriber, settings.SENSOR_MQTT_BROKER, settings.SENSOR_MQTT_PORT)
    connect_with_retry(client_publisher, settings.CLOUD_MQTT_BROKER, settings.CLOUD_MQTT_PORT)

    # Start MQTT loops
    client_subscriber.loop_start()
    client_publisher.loop_start()

    # Start periodic data fetching & publishing thread
    threading.Thread(target=fetch_reduce_and_publish, daemon=True).start()

# Graceful Shutdown
def stop():
    logging.info("👋 [EXITING] Disconnecting MQTT clients...")
    client_subscriber.loop_stop()
    client_publisher.loop_stop()
    client_subscriber.disconnect()
    client_publisher.disconnect()
    logging.info("✅ [EXITED] Clean shutdown completed.")

# Allow direct execution for debugging
if __name__ == "__main__":
    try:
        run()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
