from flask import Flask, request, jsonify
from app.logging import save_to_json_log
from datetime import datetime
from collections import deque
import time
import logging

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
    return "Welcome to secure portal", 200

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
                "attacker_ip": attacker_ip,
                "user_agent": user_agent,
                "http-method": request.method,
                "signature": "Potential BruteForce",
                "pot_name": "Brute Force pot"
            }

            save_to_json_log(attack_info)

    return jsonify({
        "status": "error",
        "message": "Invalid credentials"
    }), 401