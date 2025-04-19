import os
import logging
import joblib
import numpy as np
import tensorflow as tf
from sklearn.ensemble import RandomForestRegressor
from app import app

DEVICES = [
    'Fridge_kWh', 'Washer_kWh', 'TV_kWh', 'Lights_kWh',
    'Toaster_kWh', 'Router_kWh', 'Charger_kWh', 'Vacuum_kWh', 'Kettle_kWh'
]

MODEL_DIR = "saved_model" 

# dummy data if no model found 
def create_dummy_consumption_model():
   
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    X = np.array([[50, 3, 2], [100, 4, 3], [150, 5, 4]])  
    y = np.array([5.0, 8.0, 12.0]) 
    model.fit(X, y)
    return model

def create_dummy_power_model():
    inputs = tf.keras.Input(shape=(1, 10))  
    x = tf.keras.layers.LSTM(16)(inputs)
    outputs = tf.keras.layers.Dense(1)(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mse')
    return model

def load_models():
    logging.info(f"Loading models from directory: {MODEL_DIR}")
    consumption_models = {}
    models_loaded = True
    
    for device in DEVICES:
        try:
            model_path = f"{MODEL_DIR}/{device}_model.pkl"
            logging.info(f"Loading model for {device} from {model_path}")
            consumption_models[device] = joblib.load(model_path)
        except FileNotFoundError:
            logging.warning(f"Model file not found for {device} at {model_path}, creating dummy model")
            consumption_models[device] = create_dummy_consumption_model()
            models_loaded = False
        except Exception as e:
            logging.warning(f"Error loading model for {device}: {e}, creating dummy model")
            consumption_models[device] = create_dummy_consumption_model()
            models_loaded = False

    # Try to load power generation model, or create dummy model
    power_model = None
    try:
        power_model_path = f"{MODEL_DIR}/best_BLSTM_regression_model.keras"
        logging.info(f"Loading power generation model from {power_model_path}")
        power_model = tf.keras.models.load_model(power_model_path)
    except FileNotFoundError:
        logging.warning(f"Power generation model file not found at {power_model_path}, creating dummy model")
        power_model = create_dummy_power_model()
        models_loaded = False
    except Exception as e:
        logging.warning(f"Error loading power generation model: {e}, creating dummy model")
        power_model = create_dummy_power_model()
        models_loaded = False

    if not models_loaded:
        logging.warning("Using dummy models for demonstration. Predictions will not be accurate.")
    else:
        logging.info("All models loaded successfully")
        
    return consumption_models, power_model
