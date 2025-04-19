import logging
import requests
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from app import app
from dotenv import load_dotenv
import os

load_dotenv()

# Constants
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_FORECAST_URL = "http://api.weatherapi.com/v1/forecast.json"
IP_GEO_API_URL = "http://ip-api.com/json"

POWER_FEATURE_NAMES = [
    "temperature_2m", "relativehumidity_2m", "direct_radiation",
    "diffuse_radiation", "windspeed_10m", "cloudcover",
    "month_sin", "month_cos", "season_sin", "season_cos"
]

def detect_city_by_ip() -> Optional[str]:
    try:
        logging.info("Detecting city by IP address")
        response = requests.get(IP_GEO_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        city = data.get("city")
        if city and data.get("status") == "success":
            logging.info(f"Detected city: {city}")
            return city
        else:
            logging.warning(f"IP Geolocation status: {data.get('status')}. Could not detect city.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error detecting city via IP: {e}")
        return None

def get_forecast_weather_data(city: str, days: int = 4) -> Optional[List[Dict[str, Any]]]:

    logging.info(f"Getting weather forecast for {city} for {days} days")
    
    if not WEATHER_API_KEY:
        logging.error("Weather API Key is not configured")
        return None

    params = {"key": WEATHER_API_KEY, "q": city, "days": days, "aqi": "no", "alerts": "no"}
    try:
        response = requests.get(WEATHER_FORECAST_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "forecast" not in data or "forecastday" not in data["forecast"]:
            logging.error(f"Unexpected API response format for {city}. Missing 'forecast' data.")
            return None

        daily_features_list = []

        for day_forecast in data["forecast"]["forecastday"]:
            day_data = day_forecast.get("day", {})
            date_str = day_forecast.get("date")
            if not date_str or not day_data:
                logging.warning(f"Skipping forecast day due to missing data for {city} on {date_str}")
                continue

            direct_radiation = 500.0  # Placeholder (W/m^2)
            diffuse_radiation = 200.0  # Placeholder (W/m^2)

            temperature_2m = day_data.get("avgtemp_c")
            relativehumidity_2m = day_data.get("avghumidity")
            windspeed_10m = day_data.get("maxwind_kph", 0) / 3.6  # km/h to m/s
            
            # Estimate average cloud cover
            cloudcover_percent = day_data.get("avgvis_km")
            if 'hour' in day_forecast and not cloudcover_percent:
                hourly_clouds = [h.get('cloud', 50) for h in day_forecast['hour']]
                cloudcover_percent = sum(hourly_clouds) / len(hourly_clouds) if hourly_clouds else 50

            if temperature_2m is None: 
                logging.warning(f"Missing avg temp for {date_str}, using placeholder.")
                temperature_2m = 15.0
            if relativehumidity_2m is None: 
                logging.warning(f"Missing avg humidity for {date_str}, using placeholder.")
                relativehumidity_2m = 60.0
            if cloudcover_percent is None: 
                logging.warning(f"Missing cloud cover for {date_str}, using placeholder.")
                cloudcover_percent = 50.0

            cloudcover = cloudcover_percent / 100.0  

            dt = datetime.strptime(date_str, "%Y-%m-%d")
            month = dt.month
            season = (month % 12 + 3) // 3 

            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            season_sin = np.sin(2 * np.pi * season / 4)
            season_cos = np.cos(2 * np.pi * season / 4)

            features = [
                temperature_2m, relativehumidity_2m, direct_radiation,
                diffuse_radiation, windspeed_10m, cloudcover,
                month_sin, month_cos, season_sin, season_cos
            ]

            if any(f is None for f in features):
                logging.warning(f"Skipping day {date_str} due to missing essential feature values after processing.")
                continue

            daily_features_list.append({"date": date_str, "features": features})

        if not daily_features_list:
            logging.error(f"Could not extract any valid forecast days for {city}.")
            return None

        logging.warning("Using placeholder solar radiation values for all forecast days.")

        return daily_features_list

    except requests.exceptions.Timeout:
        logging.error(f"Timeout fetching weather forecast for {city}.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather forecast for {city}: {e}")
        return None
    except KeyError as e:
        logging.error(f"Unexpected weather forecast data format from API for {city}: Missing key {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during forecast processing: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None
