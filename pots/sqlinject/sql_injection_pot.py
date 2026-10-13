from flask import Flask, request, jsonify, render_template
from datetime import datetime
import re
import logging
import requests

logging.basicConfig(
    filename='pots/honeypot.log',
    level=logging.INFO,
    format='%(asctime)s -%(message)s'
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('FAKE_login.html')

@app.route("/auth/login", methods=["POST", "GET"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if re.search(r'[\'"\s]+(or|and)\b', username or password, re.IGNORECASE):
        attack_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
            'method': 'POST',
            'user_agent': request.headers.get('user-agent'),
            'pot_name': 'sql_injection_pot',
            'payload' : f"user={username}&pass={password}"
        }

        try:
            requests.post("http://center-backend:8000/api/v1/telemetry", json=attack_info, timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"Center connection error: {e}")

        return jsonify({
            "status": "error",
            "message": "Invalid credentials"
        }), 401