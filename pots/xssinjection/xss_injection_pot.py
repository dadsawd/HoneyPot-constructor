from flask import Flask, request, render_template, jsonify
from datetime import datetime
import logging
import re
import requests

logging.basicConfig(
    filename='honeypot.log',
    level=logging.INFO,
    format='%(asctime)s - %(messages)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('comment_trap.html')

@app.route('/comments', methods=['POST', 'GET'])
def catch_comments():
    user_input = request.form.get('comment', '') or request.args.get('q', '')
    if re.findall(r'script|on\w+=|javascript:', user_input, re.IGNORECASE):
        attack_info = {
            "timestamp": datetime.now().isoformat(),
            'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
            "user_agent": request.headers.get('User-Agent'),
            "method": request.method,
            "signature": "Potential XSS-Injection",
            "pot_name": "XSS-Injection Pot"
        }

        try:
            requests.post("http://center-backend:8000/api/v1/telemetry", json=attack_info, timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"Center connection error: {e}")

        logging.info(f"Potential XSS-Injection attemp from {request.remote_addr}, {user_input}")

        return jsonify({
          "status": "error",
            "message": "Invalid credentials"
        }), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
