import logging
import threading
import settings
import pubsub
import outlier
import reduction
import inference
import time

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    try:
        logging.info("🚀 Starting Edge Data Processing Pipeline...")

        # Initialize Inference Module
        logging.info("🧠 Initializing Inference Module...")
        inference.run()

        # Initialize Outlier Detection Module
        logging.info("🔍 Initializing Outlier Detection Module...")
        outlier.run()

        # Initialize Dimensionality Reduction Module
        logging.info("📉 Initializing Dimensionality Reduction Module...")
        reduction.run()

        # Start MQTT PubSub Module in a separate thread
        logging.info("📡 Starting MQTT PubSub Module in a background thread...")
        mqtt_thread = threading.Thread(target=pubsub.run, daemon=True)
        mqtt_thread.start()

        # Keep main process running
        while True:
            time.sleep(1)

    except Exception as e:
        logging.error(f"❌ Critical Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()

