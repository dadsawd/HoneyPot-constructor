# app/main.py
import json
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from json_logging import save_to_json_log
from database import databaze

app = Flask(__name__)
# Включаем CORS, чтобы браузер не блокировал сетевые запросы фронтенда к бэкенду

active_traps = []

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Инициализируем сокеты для реалтайм передачи логов на экран друга
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    databaze.init_db()
    return render_template("UI.html")


# ===================================================
# ФИЧА 1: ДИНАМИЧЕСКИЙ ДЕПЛОЙ ЛОВУШЕК ИЗ КОНСТРУКТОРА
# ===================================================
@app.route('/api/v1/deploy', methods=['POST'],strict_slashes=False)
def deploy_pot():
    config_from_site = request.json
    if not config_from_site:
        return jsonify({"status": "error", "message": "Конфигурация пуста"}), 400

    port = config_from_site.get("port")
    container_name = f"custom_pot_{port}"
    config_string = json.dumps(config_from_site)

    # Системный вызов Docker: разворачиваем универсальный образ на выбранном порту,
    # прокидывая JSON-чертеж прямо в переменную окружения (ENV) контейнера
    docker_command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:8000",
        "--network", "honeynet",
        "-e", f"POT_CONFIG={config_string}",
        "universal-pot-image:latest"
    ]

    try:
        # Принудительно тушим старый контейнер на этом порту, если он мешает
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        # Запускаем новый кастомный капкан на лету!
        subprocess.run(docker_command, check=True)
        print(f"[🔥 ORCHESTRATOR] Кастомный контейнер {container_name} успешно поднят на порту {port}!")

        trap_data = {
            "name": config_from_site.get("name", "Unknown-Trap"),
            "type": config_from_site.get("type", "Medium Interaction"),
            "port": config_from_site.get("port", 2222),
            "status": "online",
            "last_seen": "Только что"
        }
        active_traps.append(trap_data)

        return jsonify({"status": "success", "message": f"Ловушка на порту {port} успешно активирована!"}), 200
    except Exception as e:
        print(f"[❌ ERROR] Ошибка выполнения Docker: {e}")
        return jsonify({"status": "error", "message": f"Ошибка Docker: {str(e)}"}), 500


@app.route('/api/v1/hosts', methods=['GET'],strict_slashes=False)
def get_hosts():
    try:
        return jsonify(active_traps), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================================
# ФИЧА 2: СБОР ЛОГОВ ТЕЛЕМЕТРИИ С ДИНАМИЧЕСКИМ ПУШЕМ
# ===================================================
@app.route('/api/v1/telemetry', methods=['POST'], strict_slashes=False)
def collect_telemetry():
    attack_data = request.json
    if not attack_data:
        return jsonify({"status": "error"}), 400

    try:
        # Пишем прилетевшие данные лога в JSON и в PostgreSQL базу данных
        save_to_json_log(attack_info=attack_data)
        databaze.save_logs(pot_logs=attack_data)

        # МГНОВЕННЫЙ ПУШ НА ДАШБОРД ДРУГА: отправляем лог по веб-сокетам в реальном времени
        socketio.emit('new_attack', attack_data, broadcast=True)
        print(f"[💥 АТАКА СФИКСИРОВАНА] Передано на дашборд по WebSocket. Сигнатура: {attack_data.get('signature')}")

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Ошибка сохранения логов телеметрии: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Отслеживание WebSocket-статусов подключения
@socketio.on('connect')
def handle_connect():
    print(f"[🔌 SOCKET] Фронтенд дашборда оператора успешно подключился к живому WebSocket-каналу.")


if __name__ == '__main__':
    databaze.init_db()
    print("[🔥 CENTRAL ENGINE ACTIVE] Бэкенд и оркестратор сокетов запущены на порту 8000!")
    # Важно: для работы реалтайм сокетов запускаем сервер через socketio.run
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)
