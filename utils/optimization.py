import logging
import numpy as np
from typing import Dict, List, Tuple, Any


device_categories = {
    'Fridge': {'priority': 'essential', 'flexibility': 0.1},
    'Router': {'priority': 'essential', 'flexibility': 0.0},
    'Lights': {'priority': 'adjustable', 'flexibility': 0.5},
    'TV': {'priority': 'optional', 'flexibility': 0.9},
    'Washer': {'priority': 'shiftable', 'flexibility': 1.0},
    'Toaster': {'priority': 'optional', 'flexibility': 0.8},
    'Charger': {'priority': 'adjustable', 'flexibility': 0.6},
    'Vacuum': {'priority': 'shiftable', 'flexibility': 1.0},
    'Kettle': {'priority': 'shiftable', 'flexibility': 0.7}
}
default_category = {'priority': 'adjustable', 'flexibility': 0.5} 

def generate_hourly_profile(daily_total_kwh: float, daylight_hours: int = 12) -> List[float]:
    
    logging.info(f"Generating hourly profile for {daily_total_kwh:.2f} kWh, {daylight_hours} daylight hours")
    
    if daily_total_kwh <= 0:
        return [0.0] * 24

    hourly_generation = [0.0] * 24
    start_hour = (24 - daylight_hours) // 2
    end_hour = start_hour + daylight_hours
    daylight_profile = np.sin(np.linspace(0, np.pi, daylight_hours))
    normalized_profile = daylight_profile / np.sum(daylight_profile) if np.sum(daylight_profile) > 0 else daylight_profile

    for i in range(daylight_hours):
        hour_index = start_hour + i
        if 0 <= hour_index < 24:
            hourly_generation[hour_index] = daily_total_kwh * normalized_profile[i]

    return hourly_generation

def generate_device_hourly_profile(daily_kwh: float, device_name: str) -> List[float]:
  
    hourly_profile = [daily_kwh / 24.0] * 24
    
    if device_name == 'Fridge':
        pattern = np.array([
            0.9, 0.8, 0.8, 0.8, 0.8, 0.9,  # 0-5 (night, less door opening)
            1.0, 1.1, 1.1, 1.0, 1.0, 1.1,  # 6-11 (morning activity)
            1.2, 1.3, 1.3, 1.2, 1.1, 1.1,  # 12-17 (afternoon, warmer, more activity)
            1.0, 1.0, 1.0, 0.9, 0.9, 0.9   # 18-23 (evening, cooling down)
        ])
        
    elif device_name == 'Lights':
        # Higher usage in morning and evening
        pattern = np.array([
            0.2, 0.1, 0.1, 0.1, 0.2, 0.5,  # 0-5
            0.8, 0.9, 0.6, 0.3, 0.2, 0.2,  # 6-11
            0.2, 0.2, 0.2, 0.3, 0.5, 0.9,  # 12-17
            1.2, 1.4, 1.3, 1.0, 0.7, 0.4   # 18-23
        ])
    
    elif device_name == 'TV':
        # Higher in evening
        pattern = np.array([
            0.2, 0.1, 0.1, 0.1, 0.1, 0.2,  # 0-5
            0.3, 0.5, 0.4, 0.3, 0.4, 0.5,  # 6-11
            0.6, 0.5, 0.4, 0.6, 0.8, 1.2,  # 12-17
            2.0, 2.2, 1.8, 1.2, 0.8, 0.4   # 18-23
        ])
    
    elif device_name in ['Washer', 'Vacuum']:
        # Typically used during daytime
        pattern = np.array([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 0-5
            0.2, 0.4, 0.8, 1.2, 1.5, 1.4,  # 6-11
            1.2, 1.0, 1.2, 1.4, 1.5, 1.4,  # 12-17
            1.0, 0.6, 0.2, 0.0, 0.0, 0.0   # 18-23
        ])
    
    elif device_name == 'Router':
        # Fairly constant, slight reduction overnight
        pattern = np.array([
            0.8, 0.8, 0.8, 0.8, 0.8, 0.8,  # 0-5
            1.0, 1.1, 1.1, 1.1, 1.1, 1.1,  # 6-11
            1.1, 1.1, 1.1, 1.1, 1.1, 1.1,  # 12-17
            1.1, 1.1, 1.0, 0.9, 0.9, 0.8   # 18-23
        ])
    
    elif device_name in ['Toaster', 'Kettle']:
        # Morning and evening peaks
        pattern = np.array([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.2,  # 0-5
            1.0, 2.5, 2.0, 0.8, 0.5, 0.4,  # 6-11
            0.6, 0.5, 0.4, 0.5, 0.8, 1.0,  # 12-17
            1.2, 1.0, 0.6, 0.4, 0.2, 0.0   # 18-23
        ])
    
    elif device_name == 'Charger':
        # Evening and night charging
        pattern = np.array([
            1.2, 1.1, 1.0, 0.9, 0.8, 0.7,  # 0-5
            0.6, 0.6, 0.7, 0.8, 0.8, 0.9,  # 6-11
            0.9, 0.9, 0.9, 1.0, 1.1, 1.2,  # 12-17
            1.3, 1.5, 1.8, 2.0, 1.6, 1.4   # 18-23
        ])
    
    else:
        # Default even distribution
        pattern = np.ones(24)
    
    # Normalize the pattern
    normalized_pattern = pattern / np.sum(pattern) if np.sum(pattern) > 0 else pattern
    
    # Scale by daily total
    hourly_profile = normalized_pattern * daily_kwh
    
    return hourly_profile.tolist()

def optimize_load_schedule(
    device_consumption: Dict[str, float],
    hourly_generation: List[float]
) -> Tuple[List[Dict[str, Any]], List[float], List[float]]:
    logging.info("Optimizing load schedule")
    
    # Generate original hourly consumption profiles for each device
    device_hourly_profiles = {}
    for device, daily_kwh in device_consumption.items():
        device_hourly_profiles[device] = generate_device_hourly_profile(daily_kwh, device)
    
    # Calculate total hourly consumption (original)
    hourly_consumption = [0.0] * 24
    for device, hourly_profile in device_hourly_profiles.items():
        for hour in range(24):
            hourly_consumption[hour] += hourly_profile[hour]
    
    # Calculate total daily generation and consumption
    total_generation = sum(hourly_generation)
    total_consumption = sum(hourly_consumption)
    
    # Check energy balance
    energy_surplus = total_generation >= total_consumption
    
    # Hours with excess solar production
    excess_hours = []
    for hour in range(24):
        if hourly_generation[hour] > hourly_consumption[hour]:
            excess_hours.append(hour)
    
    # Hours with minimal or no solar production
    deficit_hours = []
    for hour in range(24):
        if hourly_generation[hour] < 0.2 * max(hourly_generation):
            deficit_hours.append(hour)
    
    # Generate optimization recommendations and optimized profiles
    recommendations = []
    optimized_profiles = {device: list(profile) for device, profile in device_hourly_profiles.items()}
    
    for device, daily_kwh in device_consumption.items():
        # Get device category and flexibility
        category = device_categories.get(device, default_category)
        priority = category['priority']
        flexibility = category['flexibility']
        
        recommendation = {
            "device": device,
            "daily_kwh": daily_kwh,
            "priority": priority,
            "flexibility": flexibility,
            "actions": []
        }
        
        if priority == 'essential':
            recommendation["actions"].append({
                "type": "info",
                "text": f"{device} is essential and has minimal flexibility for load shifting."
            })
            
        elif priority == 'shiftable' and excess_hours:
            # For shiftable loads, try to move usage to hours with excess generation
            if not energy_surplus:
                shifted_amount = min(daily_kwh * flexibility, daily_kwh * 0.7)
                
                # Reduce consumption during deficit hours
                for hour in deficit_hours:
                    reduction = optimized_profiles[device][hour] * 0.9
                    optimized_profiles[device][hour] -= reduction
                
                # Increase consumption during excess hours
                for hour in excess_hours:
                    addition = shifted_amount / len(excess_hours)
                    optimized_profiles[device][hour] += addition
                
                recommendation["actions"].append({
                    "type": "shift",
                    "text": f"Shift {device} usage to hours {', '.join(map(str, excess_hours))} when solar production is highest."
                })
            
        elif priority == 'optional' and not energy_surplus:
            # For optional loads, recommend reduction if energy deficit
            reduction_percent = 30  # Reduce by 30%
            reduced_amount = daily_kwh * (reduction_percent / 100)
            
            for hour in range(24):
                optimized_profiles[device][hour] *= (1 - reduction_percent / 100)
            
            recommendation["actions"].append({
                "type": "reduce",
                "text": f"Reduce {device} usage by {reduction_percent}% to save approximately {reduced_amount:.2f} kWh."
            })
            
        elif priority == 'adjustable':
            # For adjustable loads, provide energy-saving recommendations
            if not energy_surplus:
                recommendation["actions"].append({
                    "type": "adjust",
                    "text": f"Consider using {device} more efficiently or during high solar production periods."
                })
        
        # If no specific actions were recommended, add a general note
        if not recommendation["actions"]:
            recommendation["actions"].append({
                "type": "info",
                "text": f"Current {device} usage aligns well with your energy profile."
            })
            
        recommendations.append(recommendation)
    
    # Calculate optimized hourly consumption
    optimized_consumption = [0.0] * 24
    for device, hourly_profile in optimized_profiles.items():
        for hour in range(24):
            optimized_consumption[hour] += hourly_profile[hour]
    
    return recommendations, hourly_consumption, optimized_consumption
