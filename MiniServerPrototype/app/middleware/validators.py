from flask import request, jsonify

def validate_json(required_fields):
    """Validasi JSON body memiliki field yang diperlukan"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            data = request.get_json() or {}
            
            missing = [field for field in required_fields if field not in data or not data[field]]
            
            if missing:
                return jsonify({
                    'error': 'Field berikut diperlukan',
                    'missing_fields': missing
                }), 400
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def validate_string_length(field_name, min_len=1, max_len=200):
    """Validasi panjang string"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            data = request.get_json() or {}
            value = data.get(field_name, '')
            
            if not (min_len <= len(value) <= max_len):
                return jsonify({
                    'error': f'{field_name} harus antara {min_len} dan {max_len} karakter'
                }), 400
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
