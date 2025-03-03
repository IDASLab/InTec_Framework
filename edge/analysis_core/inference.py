import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
import settings
import outlier
import reduction
from dbmodel import db
from tensorflow.keras import backend as K

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load Settings
INFERENCE_ENABLE = settings.INFERENCE_ENABLE
STORE_ENABLE = settings.REDUCTION_ENABLE
SLIDING_WINDOW_SIZE = settings.SLIDING_WINDOW_SIZE
INFERENCE_MODEL_NAME = settings.INFERENCE_MODEL

# Model Paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
SCALER_PATH = os.path.join(MODEL_DIR, "Scaler.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, f"{INFERENCE_MODEL_NAME}.h5")

# Load Scaler Model
scaler_model = None
try:
    scaler_model = joblib.load(SCALER_PATH)
    logging.info("✅ Scaler model loaded successfully.")
except FileNotFoundError:
    logging.error(f"❌ Scaler model not found at {SCALER_PATH}.")
except Exception as e:
    logging.error(f"❌ Error loading scaler model: {e}")

# Custom Metrics for Model Loading
def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    return true_positives / (possible_positives + K.epsilon())

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    return true_positives / (predicted_positives + K.epsilon())

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + K.epsilon()))

# Load Inference Model
inference_model = None
try:
    inference_model = tf.keras.models.load_model(
        MODEL_PATH, custom_objects={"f1_m": f1_m, "precision_m": precision_m, "recall_m": recall_m}
    )
    logging.info(f"✅ Inference model '{INFERENCE_MODEL_NAME}' loaded successfully.")
except FileNotFoundError:
    logging.error(f"❌ Inference model '{INFERENCE_MODEL_NAME}' not found at {MODEL_PATH}.")
except Exception as e:
    logging.error(f"❌ Error loading inference model: {e}")

def run():
    """Initialize inference module."""
    if INFERENCE_ENABLE and inference_model:
        logging.info(f"✅ Inference module enabled with model '{INFERENCE_MODEL_NAME}'.")
    else:
        logging.warning("⚠️ Inference module is disabled or the model is unavailable.")

def scale_data(data):
    """Scale input data using the pre-loaded scaler model."""
    if scaler_model is None:
        logging.error("❌ Scaler model is not available. Cannot scale data.")
        return None

    try:
        converted_data = pd.DataFrame(data["data"]).T
        return scaler_model.transform(converted_data)
    except Exception as e:
        logging.error(f"❌ Error in scaling data: {e}")
        return None

def feed(data):
    """
    Perform inference on incoming sensor data.
    Includes outlier detection, dimensionality reduction, and prediction.
    """
    if not INFERENCE_ENABLE:
        #logging.warning("⚠️ Inference is disabled. Skipping processing.")
        return

    if inference_model is None:
        logging.error("❌ Inference model is not loaded. Cannot perform predictions.")
        return

    if "data" not in data or not isinstance(data["data"], dict):
        logging.error("❌ Invalid data format for inference. Skipping processing.")
        return

    # Step 1: Scale Data
    scaled_data = scale_data(data)
    if scaled_data is None:
        logging.error("❌ Error in scaling data. Skipping inference.")
        return

    # Step 2: Outlier Detection
    outlier_result = outlier.inference_feed(scaled_data)
    if not outlier_result["value"]:
        logging.info("✅ No significant outliers detected. Skipping further processing.")
        return

    # Step 3: Dimensionality Reduction
    reduced_data = reduction.inference_reduce_data(outlier_result["data"])
    if reduced_data is None:
        logging.error("❌ Error in dimensionality reduction. Skipping inference.")
        return

    reduced_data_np = np.expand_dims(reduced_data, axis=0)

    # Step 4: Perform Prediction
    try:
        prediction = inference_model.predict(np.array(reduced_data_np), batch_size=1)
        data["label"] = int(np.argmax(prediction))
        logging.info(f"✅ Inference completed. Predicted label: {data['label']}")
    except Exception as e:
        logging.error(f"❌ Error during inference prediction: {e}")
        return
    
# Allow module execution for debugging
if __name__ == "__main__":
    run()
