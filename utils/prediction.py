import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from utils.weather_api import get_forecast_weather_data, POWER_FEATURE_NAMES

def predict_energy_consumption(
    area: float, 
    rooms: int, 
    occupants: int, 
    selected_devices: List[str],
    consumption_models: Dict
) -> Tuple[float, Dict[str, float]]:
   
    logging.info(f"Predicting consumption for area={area}, rooms={rooms}, occupants={occupants}")
    logging.info(f"Selected devices: {selected_devices}")
    
    device_consumption = {}
    total_consumption = 0.0
    input_features = np.array([area, rooms, occupants]).reshape(1, -1)
    for device in selected_devices:
        if device in consumption_models:
            try:
                prediction = consumption_models[device].predict(input_features)[0]
                prediction = max(0.0, prediction)  
                
                device_name = device.replace('_kWh', '')
                device_consumption[device_name] = prediction
                total_consumption += prediction
                
                logging.info(f"Predicted {prediction:.2f} kWh for {device_name}")
            except Exception as e:
                logging.error(f"Error predicting consumption for {device}: {e}")
                device_name = device.replace('_kWh', '')
                device_consumption[device_name] = 0.0
        else:
            logging.warning(f"No model available for {device}")
            device_name = device.replace('_kWh', '')
            device_consumption[device_name] = 0.0
    
    logging.info(f"Total predicted consumption: {total_consumption:.2f} kWh")
    return total_consumption, device_consumption

def predict_multi_day_power_generation(
    city: str, 
    days_to_predict: int = 4,
    power_model = None
) -> Optional[List[Dict[str, Any]]]:
  
    logging.info(f"Predicting multi-day power generation for {city}, {days_to_predict} days")
    
    if power_model is None:
        logging.error("No power generation model provided")
        return None
        
    forecast_data = get_forecast_weather_data(city, days=days_to_predict)

    if forecast_data is None:
        logging.error("Failed to get forecast data")
        return None

    predictions = []
    try:
        for day_data in forecast_data:
            date_str = day_data["date"]
            weather_inputs = day_data["features"]

            if len(weather_inputs) != len(POWER_FEATURE_NAMES):
                logging.error(
                    f"Feature mismatch for date {date_str}. "
                    f"Expected {len(POWER_FEATURE_NAMES)}, got {len(weather_inputs)}."
                )
                continue

            input_data = np.array(weather_inputs).reshape(1, 1, len(POWER_FEATURE_NAMES))
            prediction_raw = power_model.predict(input_data, verbose=0)
            scaling_factor = 10.0
            predicted_kwh = float(scaling_factor * prediction_raw[0][0])
            predicted_kwh = max(0.0, predicted_kwh)
            predictions.append({"date": date_str, "prediction_kwh": predicted_kwh})
            logging.info(f"Predicted {predicted_kwh:.2f} kWh for {date_str}")

        return predictions

    except Exception as e:
        logging.error(f"Error during multi-day power prediction: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None
