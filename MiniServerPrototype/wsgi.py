#!/usr/bin/env python3
"""
WSGI config untuk production deployment dengan Gunicorn
Gunakan: gunicorn -c gunicorn_config.py wsgi:app
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
