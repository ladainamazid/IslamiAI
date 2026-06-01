from flask import request, jsonify
from app.routes import auth_bp
from app.middleware import require_api_key
from app.utils import validate_json
from app.security import create_access_token
from app.database import User

@auth_bp.route('/get-token', methods=['POST'])
@require_api_key
@validate_json(['username'])
def get_token():
    """Dapatkan access token (perlu API Key)"""
    data = request.get_json()
    username = data['username']
    
    # Validasi username
    if len(username) < 3 or len(username) > 50:
        return jsonify({
            'error': 'Username harus 3-50 karakter'
        }), 400
    
    # Cek apakah user sudah ada
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
    
    # Buat token baru
    token = create_access_token(username, duration_hours=24)
    
    return jsonify({
        'success': True,
        'token': token,
        'expires_in_hours': 24,
        'message': f'Token berhasil dibuat untuk {username}',
        'usage': {
            'example': 'Authorization: Bearer <token>',
            'header': 'X-API-Key: <your-api-key>'
        }
    }), 201
