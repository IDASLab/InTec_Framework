import os
import logging
import joblib
import pandas as pd
import numpy as np
import settings
from dbmodel import db

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load Settings
SLIDING_WINDOW_SIZE = settings.SLIDING_WINDOW_SIZE
OUTLIER_DROP_RATE = settings.OUTLIER_DROP_RATE
OUTLIER_ENABLE = settings.OUTLIER_ENABLE
OUTLIER_MODEL_NAME = settings.OUTLIER_MODEL

# Model Path
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
OUTLIER_MODEL_PATH = os.path.join(MODEL_DIR, f"{OUTLIER_MODEL_NAME}.joblib")

# Load Outlier Model
outlier_model = None
try:
    outlier_model = joblib.load(OUTLIER_MODEL_PATH)
    logging.info(f"✅ Outlier detection model '{OUTLIER_MODEL_NAME}' loaded successfully.")
except FileNotFoundError:
    logging.error(f"❌ Outlier model '{OUTLIER_MODEL_NAME}' not found at {OUTLIER_MODEL_PATH}.")
except Exception as e:
    logging.error(f"❌ Error loading outlier model: {e}")

def run():
    """Initialize the outlier detection module."""
    if OUTLIER_ENABLE and outlier_model:
        logging.info(f"✅ Outlier detection module enabled with model '{OUTLIER_MODEL_NAME}'.")
    else:
        logging.warning("⚠️ Outlier detection module is disabled or the model is unavailable.")

def feed(data):
    """
    Process incoming data and check for outliers before storing it.
    If outlier detection is disabled, stores data without validation.
    """
    if not OUTLIER_ENABLE or outlier_model is None:
        logging.warning("⚠️ Outlier detection is disabled or model is unavailable. Storing data without validation.")
        data["validation"] = "unchecked"
        data["outlier_model"] = None
        return

    # Ensure valid data format
    if "data" not in data or not isinstance(data["data"], dict):
        logging.error("❌ Invalid data format for outlier detection. Skipping processing.")
        return

    try:
        # Convert data to DataFrame
        converted_data = pd.DataFrame(data["data"]).T.to_numpy()

        # Ensure valid data for the model
        if converted_data.size == 0 or converted_data.shape[1] == 0:
            logging.warning("⚠️ Received empty or invalid data for outlier detection. Skipping processing.")
            return

        # Detect outliers
        data_validation = outlier_model.predict(converted_data)
        valid_count = np.sum(data_validation == 1)  # Count valid data points

        # Check validity threshold
        if (valid_count / SLIDING_WINDOW_SIZE) * 100 >= OUTLIER_DROP_RATE:
            data["validation"] = "checked"
            data["outlier_model"] = OUTLIER_MODEL_NAME
            data["processed"] = False
            #logging.info("✅ Data passed outlier detection and was stored.")
        else:
            logging.warning("❌ Data failed outlier validation and was discarded.")

    except Exception as e:
        logging.error(f"❌ Error during outlier detection processing: {e}", exc_info=True)

def inference_feed(data):
    """
    Perform outlier detection for inference.
    Returns {"value": True, "data": data} if valid, else {"value": False, "data": None}.
    """
    if not OUTLIER_ENABLE or outlier_model is None:
        logging.error("❌ Outlier model is not available. Cannot perform inference.")
        return {"value": False, "data": None}

    try:
        # Convert input to DataFrame if necessary
        if isinstance(data, np.ndarray):
            data = pd.DataFrame(data)

        if data.empty or data.shape[1] == 0:
            logging.warning("⚠️ Empty or invalid input for outlier detection inference.")
            return {"value": False, "data": None}

        # Perform outlier detection
        data_validation = outlier_model.predict(data)
        valid_count = np.sum(data_validation == 1)

        # Check validity threshold
        if (valid_count / SLIDING_WINDOW_SIZE) * 100 >= OUTLIER_DROP_RATE:
            return {"value": True, "data": data}
        else:
            return {"value": False, "data": None}

    except Exception as e:
        logging.error(f"❌ Error during outlier detection inference: {e}", exc_info=True)
        return {"value": False, "data": None}

# Allow module execution for debugging
if __name__ == "__main__":
    run()
