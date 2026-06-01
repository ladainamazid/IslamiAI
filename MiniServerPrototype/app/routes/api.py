from flask import request, jsonify
from app.routes import api_bp
from app.middleware import require_api_key, require_token, rate_limit
from app.database import User
from datetime import datetime

@api_bp.route('/data', methods=['GET'])
@require_api_key
@require_token
@rate_limit(max_requests=50, window_seconds=60)
def get_data():
    """Ambil data (perlu API Key + Token)"""
    user = request.current_user
    
    return jsonify({
        'success': True,
        'message': f'Halo, {user.username}!',
        'data': {
            'server': 'Mini Server Pro v2.0.0',
            'user': user.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'features': {
                'authentication': 'API Key + JWT Token',
                'rate_limiting': '50 req/menit/IP',
                'database': 'SQLite dengan SQLAlchemy',
                'security': 'HTTPS + Hashing + Validation'
            }
        },
        'metadata': {
            'api_version': '2.0.0',
            'environment': 'production'
        }
    }), 200

@api_bp.route('/users', methods=['GET'])
@require_api_key
@require_token
@rate_limit(max_requests=30, window_seconds=60)
def get_users():
    """List semua user (perlu autentikasi)"""
    users = User.query.all()
    
    return jsonify({
        'success': True,
        'count': len(users),
        'users': [user.to_dict() for user in users]
    }), 200

@api_bp.route('/echo', methods=['POST'])
@require_api_key
@require_token
def echo():
    """Echo data (untuk testing)"""
    data = request.get_json() or {}
    
    return jsonify({
        'success': True,
        'echo': data,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200
