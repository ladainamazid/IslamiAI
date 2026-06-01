import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    API_KEY = os.getenv('API_KEY', 'default-api-key')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///server.db')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    VALID_DURATION_HOURS = int(os.getenv('VALID_DURATION_HOURS', '24'))
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 50))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', 60))
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', 'ssl/cert.pem')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', 'ssl/key.pem')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
