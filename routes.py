import logging
from datetime import datetime, date, timedelta
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, EnergyProfile, Device, EnergyRecord, HourlyEnergyData, DeviceConsumption
from utils.models_loader import load_models
from utils.prediction import predict_energy_consumption, predict_multi_day_power_generation
from utils.weather_api import detect_city_by_ip, get_forecast_weather_data
from utils.optimization import optimize_load_schedule, generate_hourly_profile
from utils.ai_assistant import generate_ai_response

DEVICES = [
    'Fridge_kWh', 'Washer_kWh', 'TV_kWh', 'Lights_kWh',
    'Toaster_kWh', 'Router_kWh', 'Charger_kWh', 'Vacuum_kWh', 'Kettle_kWh'
]

consumption_models, power_model = load_models()
if consumption_models is None or power_model is None:
    logging.error("Models failed to load. Application functionality will be limited.")

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(view_func):
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        error = None
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f'User {username} is already registered.'
        elif User.query.filter_by(email=email).first() is not None:
            error = f'Email {email} is already registered.'
            
        if error is None:
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        flash(error, 'error')
        
    return render_template('register.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        error = None
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password_hash, password):
            error = 'Incorrect password.'
            
        if error is None:
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
            
        flash(error, 'error')
        
    return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
    
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    energy_profile = EnergyProfile.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        home_area = request.form.get('home_area')
        rooms = request.form.get('rooms')
        occupants = request.form.get('occupants')
        location = request.form.get('location')
        solar_capacity = request.form.get('solar_capacity')
        battery_capacity = request.form.get('battery_capacity')
        
        if energy_profile:
            energy_profile.home_area = float(home_area) if home_area else energy_profile.home_area
            energy_profile.rooms = int(rooms) if rooms else energy_profile.rooms
            energy_profile.occupants = int(occupants) if occupants else energy_profile.occupants
            energy_profile.location = location if location else energy_profile.location
            energy_profile.solar_capacity = float(solar_capacity) if solar_capacity else energy_profile.solar_capacity
            energy_profile.battery_capacity = float(battery_capacity) if battery_capacity else energy_profile.battery_capacity
        else:
            energy_profile = EnergyProfile(
                user_id=user.id,
                home_area=float(home_area) if home_area else 0,
                rooms=int(rooms) if rooms else 0,
                occupants=int(occupants) if occupants else 0,
                location=location if location else "",
                solar_capacity=float(solar_capacity) if solar_capacity else 0,
                battery_capacity=float(battery_capacity) if battery_capacity else 0
            )
            db.session.add(energy_profile)
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html', user=user, energy_profile=energy_profile)
    
@app.route('/dashboard')
@login_required
def dashboard():
    """Energy dashboard page"""
    user = get_current_user()
    
    energy_records = EnergyRecord.query.filter_by(user_id=user.id).order_by(EnergyRecord.date.desc()).limit(7).all()
    
    energy_profile = EnergyProfile.query.filter_by(user_id=user.id).first()
    
    today_record = EnergyRecord.query.filter_by(user_id=user.id, date=date.today()).first()
    
    devices = Device.query.filter_by(user_id=user.id).all()
    
    hourly_data = None
    if today_record:
        hourly_data = HourlyEnergyData.query.filter_by(record_id=today_record.id).order_by(HourlyEnergyData.hour).all()
    
    forecasted_generation = None
    forecasted_consumption = None
    
    if energy_profile:
        city = energy_profile.location
        if not city:
            city = detect_city_by_ip() or "New York"
        
        logging.debug(f"Generating forecast for city: {city}")
            
        generation_forecast = predict_multi_day_power_generation(city, 1, power_model)
        if generation_forecast and len(generation_forecast) > 0:
            forecasted_generation = generation_forecast[0]['prediction_kwh']
            logging.debug(f"Forecasted generation: {forecasted_generation} kWh")
            
        if energy_profile.home_area and energy_profile.rooms and energy_profile.occupants:
            device_types = [device.device_type for device in devices] if devices else DEVICES[:4]
            
            logging.debug(f"Predicting consumption for: area={energy_profile.home_area}, rooms={energy_profile.rooms}, occupants={energy_profile.occupants}")
            logging.debug(f"Device types: {device_types}")
            
            total_consumption, device_consumption = predict_energy_consumption(
                energy_profile.home_area, 
                energy_profile.rooms, 
                energy_profile.occupants,
                device_types,
                consumption_models
            )
            forecasted_consumption = total_consumption
            logging.debug(f"Forecasted consumption: {forecasted_consumption} kWh")

    return render_template(
        'dashboard.html',
        user=user,
        energy_profile=energy_profile,
        energy_records=energy_records,
        today_record=today_record,
        devices=devices,
        hourly_data=hourly_data,
        forecasted_generation=forecasted_generation,
        forecasted_consumption=forecasted_consumption,
        now=datetime.now(),  #pass current datetime for calendar
        timedelta=timedelta
    )

@app.route('/consumption', methods=['GET', 'POST'])
def consumption_page():
    """Energy consumption prediction page"""
    prediction_results = None
    error_message = None
    
    if request.method == 'POST':
        try:
            area = float(request.form.get('area', 0))
            rooms = int(request.form.get('rooms', 0))
            occupants = int(request.form.get('occupants', 0))
            selected_devices = request.form.getlist('devices')
            
            if area <= 0 or rooms <= 0 or occupants <= 0:
                error_message = "Please enter valid values for area, rooms, and occupants."
            elif not selected_devices:
                error_message = "Please select at least one device."
            else:
                total_consumption, device_consumption = predict_energy_consumption(
                    area, rooms, occupants, selected_devices, consumption_models
                )
                
                prediction_results = {
                    'total': total_consumption,
                    'devices': device_consumption
                }
                
                session['consumption_prediction'] = prediction_results
                
        except ValueError as e:
            error_message = f"Invalid input: {str(e)}"
        except Exception as e:
            logging.error(f"Error in consumption prediction: {str(e)}")
            error_message = "An error occurred during prediction. Please try again."
    
    return render_template(
        'consumption.html',
        devices=DEVICES,
        prediction_results=prediction_results,
        error_message=error_message
    )

@app.route('/generation', methods=['GET', 'POST'])
def generation_page():
    """Power generation prediction page"""
    prediction_results = None
    error_message = None
    city = None
    
    if 'city' not in session:
        detected_city = detect_city_by_ip()
        if detected_city:
            session['city'] = detected_city
            city = detected_city
    else:
        city = session.get('city')
    
    if request.method == 'POST':
        try:
            city = request.form.get('city')
            days = int(request.form.get('days', 4))
            
            if not city:
                error_message = "Please enter a city name."
            else:
                session['city'] = city 
                
                prediction_results = predict_multi_day_power_generation(city, days, power_model)
                
                if prediction_results is None:
                    error_message = "Unable to get predictions for the specified city."
                else:
                    session['generation_prediction'] = prediction_results
                    
        except ValueError as e:
            error_message = f"Invalid input: {str(e)}"
        except Exception as e:
            logging.error(f"Error in generation prediction: {str(e)}")
            error_message = "An error occurred during prediction. Please try again."
    
    return render_template(
        'generation.html',
        city=city,
        prediction_results=prediction_results,
        error_message=error_message
    )

@app.route('/optimization')
def optimization_page():
    consumption = session.get('consumption_prediction')
    generation = session.get('generation_prediction')
    
    if not consumption or not generation:
        return render_template(
            'optimization.html', 
            error_message="Please complete both consumption and generation predictions first."
        )
    
    first_day_generation = generation[0]['prediction_kwh'] if generation else 0
    hourly_generation = generate_hourly_profile(first_day_generation)
    recommendations, hourly_consumption, optimized_consumption = optimize_load_schedule(
        consumption['devices'], 
        hourly_generation
    )
    
    return render_template(
        'optimization.html',
        consumption=consumption,
        generation=generation,
        hourly_generation=hourly_generation,
        hourly_consumption=hourly_consumption,
        optimized_consumption=optimized_consumption,
        recommendations=recommendations
    )

@app.route('/chat', methods=['GET', 'POST'])
def chat_page():
    """AI assistant chat page"""
    if request.method == 'POST':
        try:
            query = request.form.get('query', '')
            if not query:
                return jsonify({"error": "Please enter a question."})
            consumption = session.get('consumption_prediction', {})
            generation = session.get('generation_prediction', [])
            
            response = generate_ai_response(
                query, 
                consumption=consumption,
                generation=generation
            )
            
            return jsonify({"response": response})
            
        except Exception as e:
            logging.error(f"Error in AI chat: {str(e)}")
            return jsonify({"error": "An error occurred while processing your request."})
    
    return render_template('chat.html')

@app.route('/api/hourly_profile', methods=['POST'])
def get_hourly_profile():
    try:
        daily_total = float(request.json.get('daily_total', 0))
        daylight_hours = int(request.json.get('daylight_hours', 12))
        
        if daily_total < 0 or daylight_hours < 1 or daylight_hours > 24:
            return jsonify({"error": "Invalid parameters"}), 400
            
        hourly_profile = generate_hourly_profile(daily_total, daylight_hours)
        return jsonify({"hourly_profile": hourly_profile})
        
    except Exception as e:
        logging.error(f"Error generating hourly profile: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/api/dashboard_data', methods=['GET'])
@login_required
def get_dashboard_data():
    try:
        user = get_current_user()
        
        today_record = EnergyRecord.query.filter_by(user_id=user.id, date=date.today()).first()
        energy_profile = EnergyProfile.query.filter_by(user_id=user.id).first()
        data = {
            "current_time": datetime.now().strftime("%H:%M:%S"),
            "today_date": date.today().strftime("%Y-%m-%d"),
            "has_actual_data": today_record is not None,
            "generation_kwh": None,
            "consumption_kwh": None,
            "battery_level_pct": None,
            "net_energy": None,
            "hourly_data": None,
            "is_forecast": False
        }
        
        if today_record:
            data["generation_kwh"] = today_record.generation_kwh
            data["consumption_kwh"] = today_record.consumption_kwh
            data["battery_level_pct"] = today_record.battery_level_pct
            
            if today_record.generation_kwh is not None and today_record.consumption_kwh is not None:
                data["net_energy"] = today_record.generation_kwh - today_record.consumption_kwh
            
            hourly_data = HourlyEnergyData.query.filter_by(record_id=today_record.id).order_by(HourlyEnergyData.hour).all()
            if hourly_data and len(hourly_data) > 0:
                data["hourly_data"] = [{
                    "hour": h.hour,
                    "generation_kwh": h.generation_kwh,
                    "consumption_kwh": h.consumption_kwh,
                    "battery_level_pct": h.battery_level_pct
                } for h in hourly_data]
        
        elif energy_profile:
            city = energy_profile.location
            if not city:
                city = detect_city_by_ip() or "New York"
            
            generation_forecast = predict_multi_day_power_generation(city, 1, power_model)
            if generation_forecast and len(generation_forecast) > 0:
                data["generation_kwh"] = generation_forecast[0]['prediction_kwh']
            
            devices = Device.query.filter_by(user_id=user.id).all()
            device_types = [device.device_type for device in devices] if devices else DEVICES[:4]
            
            if energy_profile.home_area and energy_profile.rooms and energy_profile.occupants:
                total_consumption, device_consumption = predict_energy_consumption(
                    energy_profile.home_area, 
                    energy_profile.rooms, 
                    energy_profile.occupants,
                    device_types,
                    consumption_models
                )
                data["consumption_kwh"] = total_consumption
            
            if data["generation_kwh"] is not None and data["consumption_kwh"] is not None:
                data["net_energy"] = data["generation_kwh"] - data["consumption_kwh"]
            
            data["battery_level_pct"] = 65.0 
            
            data["is_forecast"] = True
            
            if data["generation_kwh"] is not None:
                hourly_generation = generate_hourly_profile(data["generation_kwh"])
                
                if data["consumption_kwh"] is not None:
                    from utils.optimization import generate_device_hourly_profile
                    hourly_consumption = []
                    for i in range(24):
                        hourly_consumption.append(generate_device_hourly_profile(
                            data["consumption_kwh"] / 24, "Total")[i])
                    
                    data["hourly_data"] = []
                    for hour in range(24):
                        data["hourly_data"].append({
                            "hour": hour,
                            "generation_kwh": hourly_generation[hour],
                            "consumption_kwh": hourly_consumption[hour],
                            "battery_level_pct": None  
                        })
            
        return jsonify(data)
        
    except Exception as e:
        logging.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def manage_devices():
    """Manage user's energy devices"""
    user = get_current_user()
    devices = Device.query.filter_by(user_id=user.id).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        device_type = request.form.get('device_type')
        power_rating = request.form.get('power_rating')
        daily_usage_hours = request.form.get('daily_usage_hours')
        is_shiftable = 'is_shiftable' in request.form
        priority = request.form.get('priority', 3)
        
        if not name or not device_type:
            flash('Device name and type are required.', 'error')
        else:
            new_device = Device(
                user_id=user.id,
                name=name,
                device_type=device_type,
                power_rating=float(power_rating) if power_rating else None,
                daily_usage_hours=float(daily_usage_hours) if daily_usage_hours else None,
                is_shiftable=is_shiftable,
                priority=int(priority) if priority else 3
            )
            db.session.add(new_device)
            db.session.commit()
            flash('Device added successfully!', 'success')
            return redirect(url_for('manage_devices'))
    
    return render_template('devices.html', user=user, devices=devices)

@app.route('/devices/delete/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete a user device"""
    user = get_current_user()
    device = Device.query.filter_by(id=device_id, user_id=user.id).first_or_404()
    
    db.session.delete(device)
    db.session.commit()
    flash('Device deleted successfully!', 'success')
    return redirect(url_for('manage_devices'))

@app.route('/energy/records', methods=['GET'])
@login_required
def energy_records():
    """View energy consumption and generation records"""
    user = get_current_user()
    records = EnergyRecord.query.filter_by(user_id=user.id).order_by(EnergyRecord.date.desc()).all()
    
    return render_template('energy_records.html', user=user, records=records)

@app.route('/energy/add_record', methods=['GET', 'POST'])
@login_required
def add_energy_record():
    """Add a new energy record"""
    user = get_current_user()
    devices = Device.query.filter_by(user_id=user.id).all()
    
    if request.method == 'POST':
        record_date = request.form.get('date')
        consumption = request.form.get('consumption_kwh')
        generation = request.form.get('generation_kwh')
        grid_import = request.form.get('grid_import_kwh')
        grid_export = request.form.get('grid_export_kwh')
        battery_level = request.form.get('battery_level_pct')
        
        if not record_date:
            flash('Date is required.', 'error')
        else:
            try:
                record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
                
                existing_record = EnergyRecord.query.filter_by(user_id=user.id, date=record_date).first()
                if existing_record:
                    flash(f'A record for {record_date} already exists. Please edit the existing record.', 'error')
                else:
                    new_record = EnergyRecord(
                        user_id=user.id,
                        date=record_date,
                        consumption_kwh=float(consumption) if consumption else None,
                        generation_kwh=float(generation) if generation else None,
                        grid_import_kwh=float(grid_import) if grid_import else None,
                        grid_export_kwh=float(grid_export) if grid_export else None,
                        battery_level_pct=float(battery_level) if battery_level else None
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    
                    for device in devices:
                        device_consumption = request.form.get(f'device_{device.id}_consumption')
                        if device_consumption:
                            consumption_record = DeviceConsumption(
                                record_id=new_record.id,
                                device_id=device.id,
                                consumption_kwh=float(device_consumption)
                            )
                            db.session.add(consumption_record)
                    
                    for hour in range(24):
                        hour_consumption = request.form.get(f'hour_{hour}_consumption')
                        hour_generation = request.form.get(f'hour_{hour}_generation')
                        hour_battery = request.form.get(f'hour_{hour}_battery')
                        
                        if hour_consumption or hour_generation or hour_battery:
                            hourly_data = HourlyEnergyData(
                                record_id=new_record.id,
                                hour=hour,
                                consumption_kwh=float(hour_consumption) if hour_consumption else None,
                                generation_kwh=float(hour_generation) if hour_generation else None,
                                battery_level_pct=float(hour_battery) if hour_battery else None
                            )
                            db.session.add(hourly_data)
                    
                    db.session.commit()
                    flash('Energy record added successfully!', 'success')
                    return redirect(url_for('energy_records'))
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
    
    return render_template('add_energy_record.html', user=user, devices=devices)

@app.route('/energy/edit_record/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_energy_record(record_id):
    """Edit an existing energy record"""
    user = get_current_user()
    record = EnergyRecord.query.filter_by(id=record_id, user_id=user.id).first_or_404()
    devices = Device.query.filter_by(user_id=user.id).all()
    
    if request.method == 'POST':
        consumption = request.form.get('consumption_kwh')
        generation = request.form.get('generation_kwh')
        grid_import = request.form.get('grid_import_kwh')
        grid_export = request.form.get('grid_export_kwh')
        battery_level = request.form.get('battery_level_pct')
        
        record.consumption_kwh = float(consumption) if consumption else None
        record.generation_kwh = float(generation) if generation else None
        record.grid_import_kwh = float(grid_import) if grid_import else None
        record.grid_export_kwh = float(grid_export) if grid_export else None
        record.battery_level_pct = float(battery_level) if battery_level else None
        
        for device in devices:
            device_consumption = request.form.get(f'device_{device.id}_consumption')
            if device_consumption:
                consumption_record = DeviceConsumption.query.filter_by(
                    record_id=record.id, device_id=device.id).first()
                
                if consumption_record:
                    consumption_record.consumption_kwh = float(device_consumption)
                else:
                    new_consumption = DeviceConsumption(
                        record_id=record.id,
                        device_id=device.id,
                        consumption_kwh=float(device_consumption)
                    )
                    db.session.add(new_consumption)
        
        for hour in range(24):
            hour_consumption = request.form.get(f'hour_{hour}_consumption')
            hour_generation = request.form.get(f'hour_{hour}_generation')
            hour_battery = request.form.get(f'hour_{hour}_battery')
            
            if hour_consumption or hour_generation or hour_battery:
                hourly_record = HourlyEnergyData.query.filter_by(
                    record_id=record.id, hour=hour).first()
                
                if hourly_record:
                    hourly_record.consumption_kwh = float(hour_consumption) if hour_consumption else None
                    hourly_record.generation_kwh = float(hour_generation) if hour_generation else None
                    hourly_record.battery_level_pct = float(hour_battery) if hour_battery else None
                else:
                    new_hourly = HourlyEnergyData(
                        record_id=record.id,
                        hour=hour,
                        consumption_kwh=float(hour_consumption) if hour_consumption else None,
                        generation_kwh=float(hour_generation) if hour_generation else None,
                        battery_level_pct=float(hour_battery) if hour_battery else None
                    )
                    db.session.add(new_hourly)
        
        db.session.commit()
        flash('Energy record updated successfully!', 'success')
        return redirect(url_for('energy_records'))
    
    device_consumption = {dc.device_id: dc.consumption_kwh for dc in record.device_consumption}
    
    hourly_data = {hd.hour: {
        'consumption': hd.consumption_kwh,
        'generation': hd.generation_kwh,
        'battery': hd.battery_level_pct
    } for hd in record.hourly_data}
    
    return render_template(
        'edit_energy_record.html',
        user=user,
        record=record,
        devices=devices,
        device_consumption=device_consumption,
        hourly_data=hourly_data
    )

@app.route('/energy/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_energy_record(record_id):
    user = get_current_user()
    record = EnergyRecord.query.filter_by(id=record_id, user_id=user.id).first_or_404()
    
    db.session.delete(record)
    db.session.commit()
    flash('Energy record deleted successfully!', 'success')
    return redirect(url_for('energy_records'))
