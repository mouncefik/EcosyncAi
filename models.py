from datetime import datetime
from app import db

class User(db.Model):
    """User model for authentication and personalization"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    energy_profiles = db.relationship('EnergyProfile', backref='user', lazy=True)
    energy_records = db.relationship('EnergyRecord', backref='user', lazy=True)
    devices = db.relationship('Device', backref='user', lazy=True)

class EnergyProfile(db.Model):
    """User's energy profile with home characteristics"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    home_area = db.Column(db.Float, nullable=False)  # In square meters
    rooms = db.Column(db.Integer, nullable=False)
    occupants = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))
    solar_capacity = db.Column(db.Float)  # In kW
    battery_capacity = db.Column(db.Float)  # In kWh
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Device(db.Model):
    """User's energy-consuming devices"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    power_rating = db.Column(db.Float)  # In watts
    daily_usage_hours = db.Column(db.Float)
    is_shiftable = db.Column(db.Boolean, default=False)  # Can usage time be shifted
    priority = db.Column(db.Integer, default=3)  # 1-5, 1 being highest priority
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EnergyRecord(db.Model):
    """Daily energy consumption and generation records"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    consumption_kwh = db.Column(db.Float)  # Total consumption in kWh
    generation_kwh = db.Column(db.Float)  # Total generation in kWh
    grid_import_kwh = db.Column(db.Float)  # Energy imported from grid in kWh
    grid_export_kwh = db.Column(db.Float)  # Energy exported to grid in kWh
    battery_level_pct = db.Column(db.Float)  # Battery level at end of day (%)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    hourly_data = db.relationship('HourlyEnergyData', backref='daily_record', lazy=True)
    device_consumption = db.relationship('DeviceConsumption', backref='daily_record', lazy=True)

class HourlyEnergyData(db.Model):
    """Hourly breakdown of energy data"""
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('energy_record.id'), nullable=False)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    consumption_kwh = db.Column(db.Float)
    generation_kwh = db.Column(db.Float)
    battery_level_pct = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeviceConsumption(db.Model):
    """Per-device daily consumption breakdown"""
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('energy_record.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    consumption_kwh = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to get device info
    device = db.relationship('Device')