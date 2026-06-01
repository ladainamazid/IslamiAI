from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Konfigurasi
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///server.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['RATE_LIMIT_MAX'] = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 50))
    app.config['RATE_LIMIT_WINDOW'] = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', 60))
    
    # Inisialisasi database
    db.init_app(app)
    
    # Register blueprints (routes)
    from app.routes import auth_bp, api_bp, health_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(health_bp)
    
    # Buat tabel jika belum ada
    with app.app_context():
        db.create_all()
    
    return app
