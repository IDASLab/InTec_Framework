import os
import logging
import settings
import joblib
import pandas as pd
import tensorflow as tf

# Configure Logging
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Settings
REDUCTION_ENABLE = settings.REDUCTION_ENABLE
REDUCTION_MODEL_NAME = settings.REDUCTION_MODEL

# Model Paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
PCA_PATH = os.path.join(MODEL_DIR, "PCA.joblib")
AE_PATH = os.path.join(MODEL_DIR, "encoder.h5")

# Global Model Variable
reduction_model = None

def model_selector(model_name):
    """Loads the appropriate dimensionality reduction model (PCA or AE)."""
    try:
        if model_name == "PCA":
            logging.info("✅ PCA selected as reduction model.")
            return joblib.load(PCA_PATH)
        elif model_name == "AE":
            logging.info("✅ Auto-Encoder (AE) selected as reduction model.")
            return tf.keras.models.load_model(AE_PATH)
        else:
            logging.error(f"❌ '{model_name}' is not supported! Please set it as 'PCA' or 'AE'.")
            return None
    except Exception as e:
        logging.error(f"❌ Error loading {model_name} model: {e}")
        return None

def reduce_data(data):
    """
    Performs dimensionality reduction on data using the selected model.
    Returns JSON-formatted reduced data.
    """
    if not REDUCTION_ENABLE or reduction_model is None:
        logging.warning("⚠️ Dimensionality reduction is disabled or model is unavailable.")
        return None

    try:
        converted_data = pd.DataFrame(data).T.to_numpy()

        if REDUCTION_MODEL_NAME == "PCA":
            #logging.info("🔹 Running PCA Reduction...")
            reduced_data = pd.DataFrame(reduction_model.transform(converted_data))
        elif REDUCTION_MODEL_NAME == "AE":
            #logging.info("🔹 Running AutoEncoder Reduction...")
            reduced_data = pd.DataFrame(reduction_model.predict(converted_data))
        else:
            logging.error("❌ Invalid reduction model.")
            return None

        return reduced_data.to_json(orient="index")
    except Exception as e:
        logging.error(f"❌ Error during dimensionality reduction: {e}")
        return None

def inference_reduce_data(data):
    """
    Performs dimensionality reduction for inference.
    Returns a Pandas DataFrame of reduced features.
    """
    if reduction_model is None:
        logging.error("❌ Reduction model is not loaded. Cannot perform reduction.")
        return None

    try:
        if REDUCTION_MODEL_NAME == "PCA":
            logging.info("🔹 Running PCA Reduction for Inference...")
            return pd.DataFrame(reduction_model.transform(data))
        elif REDUCTION_MODEL_NAME == "AE":
            logging.info("🔹 Running AutoEncoder Reduction for Inference...")
            return pd.DataFrame(reduction_model.predict(data))
        else:
            logging.error("❌ Invalid reduction model.")
            return None
    except Exception as e:
        logging.error(f"❌ Error during inference dimensionality reduction: {e}")
        return None

def run():
    """
    Initializes the reduction module by loading the appropriate model.
    """
    global reduction_model
    if REDUCTION_ENABLE:
        reduction_model = model_selector(REDUCTION_MODEL_NAME)
    else:
        logging.warning("⚠️ Dimensionality Reduction is disabled.")

# Initialize the model only when executed directly
if __name__ == "__main__":
    run()

