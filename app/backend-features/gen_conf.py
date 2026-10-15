import json
import subprocess
import requests.exceptions
from flask import Flask, jsonify
from flask_cors import CORS
from app.database import databaze

app = Flask(__name__)
CORS(app)

@app.route('/api/v1/deploy', methods=['POST'])
def deploy_pot():
    config_from_site = requests.json
    if not config_from_site:
        return jsonify({"message": "No config from site"})
    port = config_from_site.get['port']
    attack_type = config_from_site.get['attaack_type']
    container_name = f"custom_pot_{port}"
    config_string = json.dumps(config_from_site)

    if attack_type in ['SQL-injection', "XSS-injection"]:
        docker_command = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:8000",
            "-v", "/root/honeyforge/templates:/app/templates:ro",
            "-e", f"POT_CONFIG={config_string}",
            "--network", "honeynet",
            "universal-pot-image:latest"
        ]
    else:
        docker_command = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:{port}",
            "-e", f"POT_CONFIG={config_string}",
            "--network", "honeynet",
            "universal-socket-image:latest"
        ]
    try:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output = True)
        subprocess.run(docker_command, check=True)
        return jsonify({"status": "success", "messages":f"ловушка на порту {port} активирована"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка деплоя Docker: {str(e)}"}), 500

@app.route('/api/v1/telemetry', methods=['POST'])
def get_telemetry():
    attack_data = request.json
    if not attack_data:
        return jsonify({"status":"error"}), 400

    try:
        databaze.save_logs(pot_logs=attack_data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    databaze.init_db()
    app.run(host='0.0.0.0', port=8000)