from flask import Flask, request, jsonify, render_template
from datetime import datetime
from collections import deque
import time
import logging
import requests

logging.basicConfig(
    filename='pots/honeypot.log',
    level=logging.INFO,
    format='%(asctime)s  - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

app = Flask(__name__)

attack_tracker = {}

delay = 0.1

@app.route('/')
def index():
    return render_template('fake_login.html')

@app.route('/auth/login', methods=['POST'])
def login():
    attacker_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'unknown')
    current_time = time.time()

    if attacker_ip not in attack_tracker:
        attack_tracker[attacker_ip] = deque(maxlen=5)

    attack_tracker[attacker_ip].append(current_time)
    timestamps = list(attack_tracker[attacker_ip])

    logging.info(f"Login attemp from {attacker_ip} | User: {user_agent}")

    if len(timestamps) > 1:
        last_delay = timestamps[-1] - timestamps[-2]
        if last_delay > delay:
            attack_info = {
                "timestamp": datetime.now().isoformat(),
                'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
                "user_agent": user_agent,
                "http-method": request.method,
                "signature": "Potential BruteForce",
                "pot_name": "Brute Force pot"
            }

            try:
                requests.post("http://center-backend:8000/api/v1/telemetry", json=attack_info, timeout=2)
            except requests.exceptions.RequestException as e:
                print(f"Center connection error: {e}")

    return jsonify({
        "status": "error",
        "message": "Invalid credentials"
    }), 401