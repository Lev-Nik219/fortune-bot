import os
import sys
import time
import threading
from flask import Flask, jsonify

# Проверяем версию Python
print(f"Python version: {sys.version}")

# Создаем Flask приложение
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'python_version': sys.version
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port)