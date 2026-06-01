import secrets
import hashlib
from datetime import datetime, timedelta
from app.database import Token, User
from app import db

def generate_api_key():
    """Generate API key yang aman"""
    return secrets.token_hex(32)

def generate_token():
    """Generate access token yang aman"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key):
    """Hash API key untuk penyimpanan aman"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def validate_api_key(api_key):
    """Validasi API key (di production, cek database)"""
    from app.config import Config
    return api_key == Config.API_KEY

def create_access_token(username, duration_hours=24):
    """Buat access token baru untuk user"""
    from app.config import Config
    
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    
    token = Token(
        token=generate_token(),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
    )
    db.session.add(token)
    db.session.commit()
    
    return token.token

def validate_access_token(token):
    """Validasi access token"""
    token_obj = Token.query.filter_by(token=token, is_active=True).first()
    
    if not token_obj:
        return None
    
    if token_obj.is_expired():
        token_obj.is_active = False
        db.session.commit()
        return None
    
    return token_obj.user
