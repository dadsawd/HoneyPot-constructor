from flask import Flask, request
from app.logging import save_to_json_log
from datetime import datetime
import logging
import re

logging.basicConfig(
    filename='pots/honeypot.log',
    level=logging.INFO,
    format='%(asctime)s - %(messages)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

app = Flask(__name__)

@app.route('/comments', methods=['POST', 'GET'])
def catch_comments(): # catch Stored XSS
    user_input = request.form.get('comment', '') or request.args.get('q', '')
    if re.findall(r'script|on\w+=|javascript:', user_input, re.IGNORECASE):
        attack_info = {
            "timestamp": datetime.now().isoformat(),
            "attacker_ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "http-method": request.method,
            "signature": "Potential XXS-Injection",
            "pot_name": "XSS-Injection Pot"
        }
        save_to_json_log(attack_info)

        logging.info(f"Potential XSS-Injection attemp from {request.remote_addr}, {user_input}")