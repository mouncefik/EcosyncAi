import os
import logging
from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)

# Configure session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.secret_key = os.environ.get("SESSION_SECRET", "development-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_UkDP38AYlcty@ep-billowing-king-a4oo5vgh.us-east-1.aws.neon.tech/neondb?sslmode=require")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
Session(app)
db.init_app(app)

# Load environment variables
app.config["WEATHER_API_KEY"] = os.environ.get("WEATHER_API_KEY", "b37e3983fbf14744a0b185648251104")
app.config["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY", "AIzaSyCy5SrFyq7knvb8Xu82xOOG9msoT37WFxY")
app.config["MODEL_DIR"] = "saved_model"
