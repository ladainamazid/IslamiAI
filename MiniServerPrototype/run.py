#!/usr/bin/env python3
"""
Entry point untuk menjalankan Mini Server Pro
Gunakan: python3 run.py
"""

import os
import sys
from app import create_app
from app.database import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Buat app
app = create_app()

@app.cli.command('init-db')
def init_db():
    """Inisialisasi database"""
    db.create_all()
    print('✅ Database berhasil diinisialisasi!')

@app.cli.command('seed')
def seed():
    """Buat user admin untuk testing"""
    from app.database import User
    from app.security import generate_api_key
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        db.session.add(admin)
        db.session.commit()
        print('✅ User admin berhasil dibuat!')
    else:
        print('ℹ️  User admin sudah ada')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    print("=" * 70)
    print("🚀 MINI SERVER PRO - ENTRY POINT")
    print("=" * 70)
    print(f"📌 Environment: {'Development' if debug else 'Production'}")
    print(f"🌐 Running on: http://127.0.0.1:{port}")
    print(f"🔑 API Key: {os.getenv('API_KEY', 'Not set')}")
    print("\n📌 Endpoints:")
    print("   GET  /health              → Health check (publik)")
    print("   POST /auth/get-token      → Dapatkan token (perlu API Key)")
    print("   GET  /api/data            → Akses data (perlu API Key + Token)")
    print("   GET  /api/users           → List user (perlu autentikasi)")
    print("   POST /api/echo            → Echo testing (perlu autentikasi)")
    print("=" * 70)
    
    app.run(host='127.0.0.1', port=port, debug=debug, threaded=True)
