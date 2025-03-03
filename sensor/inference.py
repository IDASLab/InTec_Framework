import numpy as np
import tflite_runtime.interpreter as tflite
import os
import time
import pandas as pd
import joblib
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# Load environment variables safely
def get_env_variable(var_name, default_value, convert_func=str):
    """Fetch environment variable and convert to correct type."""
    value = os.getenv(var_name, default_value)
    try:
        return convert_func(value.strip('"'))
    except ValueError:
        print(f"⚠️ Warning: Invalid value for {var_name}. Using default: {default_value}")
        return default_value

# Get parameters from environment variables
sensor_name = get_env_variable("Name", "sensor01")
subject = get_env_variable("Subject", "default_subject")
mqtt_broker = get_env_variable("Broker", "192.168.1.20")
mqtt_topic = get_env_variable("Topic", "sensor/data")
window_size = get_env_variable("WindowSize", 25, int)
sampling_rate = get_env_variable("Rate", 50, int)
work_time = get_env_variable("Time", 60, int) * 60  # Convert minutes to seconds

# Define paths
data_path = os.path.join("data", subject)
scaler_file = "model/Scaler.joblib"
model_file = "model/model.tflite"

# Ensure data path exists
if not os.path.exists(data_path):
    print(f"⚠️ Warning: Data path '{data_path}' does not exist. Creating it now.")
    os.makedirs(data_path, exist_ok=True)

# Ensure model exists
if not os.path.exists(model_file):
    raise FileNotFoundError(f"❌ Error: Model file '{model_file}' not found!")

# List sensor data files
list_of_sensor_data_file = os.listdir(data_path) if os.path.exists(data_path) else []
if not list_of_sensor_data_file:
    print(f"⚠️ Warning: No sensor data files found in '{data_path}'.")

# Start measuring execution time
print("📡 IoT device activated.", 
      f"\n✅ Device Name: {sensor_name}",
      f"\n📊 Sampling Data: {subject}",
      f"\n🔗 MQTT Broker: {mqtt_broker}",
      f"\n📡 Topic: {mqtt_topic}",
      f"\n🔄 Inference Window Size: {window_size}",
      f"\n⏳ Sampling Rate: {sampling_rate} Hz",
      f"\n🕒 Execution Time: {work_time / 60} mins")

start_work = time.time()

def load_to_json(data, class_label_array, n_fields, latency, sliding_window=25):
    """Convert processed data into JSON format for MQTT."""
    x_json = pd.DataFrame(data.reshape(n_fields, sliding_window)).to_json(force_ascii=False)
    x_json = json.loads(x_json)
    
    return {
        "device": sensor_name,
        "date": str(datetime.now()),
        "windowSize": sliding_window,
        "data": x_json,
        "label": int(class_label_array.argmax() + 1),  # Get predicted label
        "latency": float(latency)
    }

def run_model_on_simulated_data():
    """Run the inference model on sensor data and publish results via MQTT."""
    try:
        # Initialize MQTT client
        client = mqtt.Client(client_id=sensor_name, protocol=mqtt.MQTTv311)
        client.connect(mqtt_broker)

        # Load scaler model
        try:
            scaler_model = joblib.load(scaler_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Error: Scaler file '{scaler_file}' not found!")

        # Load TFLite model
        interpreter = tflite.Interpreter(model_path=model_file)
        interpreter.allocate_tensors()

        # Get input/output tensors
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        list_of_data = []

        while True:
            for path in list_of_sensor_data_file:
                # Watchdog: Check execution time
                if time.time() - start_work > work_time:
                    print(f"🔴 {sensor_name} is done. Runtime was {work_time / 60} minutes.")
                    return 

                if len(list_of_data) == window_size:
                    # Prepare input data for model
                    input_data = np.array(list_of_data).reshape(1, window_size, 23)

                    # Measure inference latency
                    start_latency = time.time()

                    # Run inference
                    interpreter.set_tensor(input_details[0]['index'], input_data.astype('float32'))
                    interpreter.invoke()
                    output_data = interpreter.get_tensor(output_details[0]['index'])

                    # Stop latency measurement
                    inference_latency = (time.time() - start_latency) * 1000  # Convert to ms

                    # Create JSON message
                    msg = load_to_json(input_data, output_data, 23, inference_latency, window_size)
                    print(f"📡 {sensor_name} published message on {mqtt_topic} -> "
                          f"Window: {msg['windowSize']}, Date: {msg['date']}, "
                          f"Label: {msg['label']}, Latency: {msg['latency']:.2f} ms")

                    # Publish to MQTT
                    client.publish(mqtt_topic, json.dumps(msg))

                    # Reset data list
                    list_of_data = []

                    # Sleep (based on sampling rate)
                    time.sleep(window_size / sampling_rate)

                else:
                    # Read and process data
                    file_path = os.path.join(data_path, path)
                    if os.path.exists(file_path):
                        data_stream = np.load(file_path, allow_pickle=True)
                        data_stream = scaler_model.transform(data_stream)
                        list_of_data.append(data_stream)
                    else:
                        print(f"⚠️ Warning: Missing data file '{file_path}', skipping.")

    except Exception as e:
        print(f"❌ Error in execution: {e}")

# Run the simulation
if __name__ == "__main__":
    run_model_on_simulated_data()

