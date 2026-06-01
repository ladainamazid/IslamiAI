from flask import jsonify
from datetime import datetime
from app.routes import health_bp
import psutil

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (publik)"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'server': {
            'name': 'Mini Server Pro',
            'version': '2.0.0',
            'environment': 'Linux Mint'
        },
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available // (1024 * 1024)
        }
    }), 200
