#!/usr/bin/env python3
"""
Script untuk inisialisasi database
Gunakan: python3 migrations/init_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.database import User, Token

def init_database():
    """Inisialisasi database dengan tabel"""
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print('✅ Tabel database berhasil dibuat!')
        print('   - User')
        print('   - Token')

if __name__ == '__main__':
    init_database()
