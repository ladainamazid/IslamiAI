from functools import wraps
from flask import request, jsonify
from app.security import validate_api_key, validate_access_token

def require_api_key(f):
    """Middleware: Wajib punya API Key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API Key diperlukan di header X-API-Key'}), 401
        
        if not validate_api_key(api_key):
            return jsonify({'error': 'API Key tidak valid'}), 401
        
        return f(*args, **kwargs)
    return decorated

def require_token(f):
    """Middleware: Wajib punya valid access token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token diperlukan dalam format: Bearer <token>'}), 401
        
        token = auth_header.replace('Bearer ', '')
        user = validate_access_token(token)
        
        if not user:
            return jsonify({'error': 'Token tidak valid atau kadaluarsa'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated
