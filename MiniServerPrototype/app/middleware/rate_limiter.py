from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict

request_log = defaultdict(list)

def rate_limit(max_requests=None, window_seconds=None):
    """Middleware: Rate limiting per IP"""
    from app.config import Config
    
    if max_requests is None:
        max_requests = Config.RATE_LIMIT_MAX_REQUESTS
    if window_seconds is None:
        window_seconds = Config.RATE_LIMIT_WINDOW_SECONDS
    
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Hapus request lama
            request_log[client_ip] = [
                t for t in request_log[client_ip]
                if t > window_start
            ]
            
            # Cek limit
            if len(request_log[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Terlalu banyak permintaan',
                    'retry_after': window_seconds
                }), 429
            
            # Catat request
            request_log[client_ip].append(now)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
