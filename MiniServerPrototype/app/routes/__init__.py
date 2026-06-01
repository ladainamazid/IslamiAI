from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)
health_bp = Blueprint('health', __name__)

from app.routes import auth, api, health

__all__ = ['auth_bp', 'api_bp', 'health_bp']
