import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🚀 General Settings
CLIENT_ID = os.getenv("CLIENT_ID", "Edge_UB01")

# 🏷️ Inference Model Configuration
INFERENCE_ENABLE = os.getenv("INFERENCE_ENABLE", "False").lower() == "true"
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "CNN_LSTM")  # Options: CNN, LSTM, CNN_LSTM, FFNN
SLIDING_WINDOW_SIZE = int(os.getenv("SLIDING_WINDOW_SIZE", 25))  # Options: 25, 50, 100

# 🔍 Outlier Detection Configuration
OUTLIER_ENABLE = os.getenv("OUTLIER_ENABLE", "True").lower() == "true"
OUTLIER_MODEL = os.getenv("OUTLIER_MODEL", "IsolationForest")  # Options: IsolationForest
OUTLIER_DROP_RATE = int(os.getenv("OUTLIER_DROP_RATE", 80))

# 📉 Dimensionality Reduction Configuration
REDUCTION_ENABLE = os.getenv("REDUCTION_ENABLE", "True").lower() == "true"
REDUCTION_MODEL = os.getenv("REDUCTION_MODEL", "PCA")  # Options: PCA, AE

# 🌐 Sensor MQTT Broker (For Incoming Sensor Data)
SENSOR_MQTT_BROKER = os.getenv("SENSOR_MQTT_BROKER", "intec-emqx-broker")
SENSOR_MQTT_PORT = int(os.getenv("SENSOR_MQTT_PORT", 1883))
SENSOR_MQTT_TOPIC = os.getenv("SENSOR_MQTT_TOPIC", "prediction")

# ☁️ Cloud MQTT Broker (For Processed Data)
CLOUD_MQTT_BROKER = os.getenv("CLOUD_MQTT_BROKER", "intec-emqx-broker")
CLOUD_MQTT_PORT = int(os.getenv("CLOUD_MQTT_PORT", 1883))
CLOUD_MQTT_TOPIC = os.getenv("CLOUD_MQTT_TOPIC", "cloud/processed_data")
TRAINING_MQTT_TOPIC = os.getenv("TRAINING_MQTT_TOPIC", "cloud/training_data")

# 🌐 Cloud Sync Period
CLOUD_SYNC_PERIOD = int(os.getenv("CLOUD_SYNC_PERIOD", 1))

# 🛢️ MongoDB Configuration
DB_URL = os.getenv("DB_URL", "mongodb://admin:admin@intec-mongo-db:27017/edge?authSource=admin")
DB_COLLECTION = os.getenv("DB_COLLECTION", "sensors")

# ⚙️ Logging & Debugging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

