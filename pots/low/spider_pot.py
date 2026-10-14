from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging

logging.basicConfig(
    filename='honey_pot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

app = Flask(__name__)

@app.route('/secret_dir', methods=['POST', 'GET'])
def robots_txt(): #если мы ловим гет запрос на директорию указанную в
    attack_info = {
        "timestamp": datetime.now().isoformat(),
        'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
        "user_agent": request.headers.get('User-Agent'),
        "method": request.method,
        "signature": "Potential XSS-Injection",
        "pot_name": "XSS-Injection Pot"
    }

    try:
        request.post("http://center-backend:8000/api/v1/telemetry" , attack_info)
    except Exception as e:
        print(f"Center connection error {e}")

    return jsonify({
        "status": "error",
        "message": "Internal Server Error"
    }),401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)