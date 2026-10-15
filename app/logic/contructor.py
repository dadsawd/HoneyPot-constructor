from datetime import datetime
from flask import Flask, request, render_template_string
from collections import deque
import re
import socket
import threading
import time
import requests

app = Flask(__name__)


class HoneyPot:
    def __init__(self, port: int, pot_name: str, risk_lvl: int) -> None:
        self.port = port
        self.pot_name = pot_name
        self.risk_lvl = risk_lvl
        self.trigger = None
        self.web = None

    def send_telemetry(self, attack_info: dict) -> None:
        """Метод отправки лога в Центр управления (Оркестратор)"""
        # Дообогащаем словарь метаданными ловушки
        attack_info["honeypot_name"] = self.pot_name
        attack_info["target_port"] = self.port
        attack_info["risk_lvl"] = self.risk_lvl


        requests.post("http://docker.internal", json=attack_info, timeout=2)
        print(f"Ловушка {self.pot_name} зафиксировала атаку с IP: {attack_info.get('attacker_ip')}")

        try:
            requests.post("http://center-backend:8000/api/v1/telemetry", json=attack_info, timeout=2)
        except Exception as e:
            print(f"Ошибка отправки телеметрии: {e}")

    def handle_request(self):
        """Главный диспетчер запросов ловушки среднего уровня взаимодействия"""
        # Собираем данные из полей ввода (логин и пароль), которые настроил юзер в WebBase
        user_input_login = request.form.get(self.web.login_field, "")
        user_input_pass = request.form.get(self.web.password_field, "")
        combined_input = f"{user_input_login} {user_input_pass}".strip()

        # 1. Проверяем триггер на задержку (Брутфорс автоматизацией / DDOS)
        attack = self.trigger.check_delay()

        # 2. Если задержка в норме, проверяем триггер на инъекции (SQLi/XSS)
        if not attack and combined_input:
            attack = self.trigger.check_input(combined_input)

        # 3. Если это обычный перебор формы, проверяем счетчик попыток входа
        if not attack:
            attack = self.trigger.check_tries_to_log()

        # Если хоть один капкан сработал — шлем телеметрию
        if attack and isinstance(attack, dict):
            attack["user_agent"] = request.headers.get("user-agent", "unknown")
            attack[
                "payload"] = f"Fields: {self.web.login_field}={user_input_login}&{self.web.password_field}={user_input_pass}"
            self.send_telemetry(attack)

        return self.web.render()

class WebBase:
    def __init__(self, url: str, login_field: str, password_field: str) -> None:
        self.url = url
        self.login_field = login_field
        self.password_field = password_field

    def render(self):
        """Фейковый HTML-шаблон, который динамически подставляет имена полей из конструктора"""
        html_template = f"""
        <form method="POST" action="{self.url}">
            <input type="text" name="{self.login_field}" placeholder="Логин" required>
            <input type="password" name="{self.password_field}" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
        """
        return render_template_string(html_template), 200

class Triggers:
    def __init__(self, endpoint: str, tries_to_login: int, http_method: str, attack_type: str, port: int) -> None:
        self.endpoint = endpoint
        self.tries_to_login = tries_to_login
        self.http_method = http_method
        self.attack_type = attack_type
        self.port = port
        self.counter = 0
        self.delay = 0.5

        self.attacker_tracker = {}

        self.pattern_database = {
            'SQL-injection': (
                r'[\'"\s]+(or|and)\b|union\s+select|select\s+.*\s+from|exec\s+\(|--',
                "Potential SQL-Injection Attempt"
            ),
            'XSS-injection': (
                r'script|on\w+\s*=|<\s*img|<\s*body|javascript:|alert\(|prompt\(',
                "Potential XSS (Cross-Site Scripting) Attack"
            ),
            'Path-Traversal': (
                r'\.\./|\.\.\\|etc/passwd|win\.ini|boot\.ini|/bin/sh|/bin/bash',
                "Path Traversal / Local File Inclusion (LFI) Attempt"
            ),
            'Fake-DB-Leak': (
                r'flag_user_dgtu|secret_admin_hash_2026|honey_flag',
                "Compromised Data Leak Triggered (Hacker uses Fake DB info)"
            )
        }

    def check_tries_to_log(self):
        """Проверка на превышение лимита попыток входа"""
        self.counter += 1
        if self.counter >= self.tries_to_login:
            print(f"Превышено количество попыток входа: {self.endpoint}, запрос № {self.counter}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "attacker_ip": request.remote_addr,
                "http_method": request.method,
                "attacker_port": request.environ.get('REMOTE_PORT'),
                "signature": "Brute Force Attempt"
            }
        return False

    def check_input(self, user_input: str):
        """Проверка на сигнатуры веб-атак (SQLi/XSS)"""
        if not self.attack_type:
            return False

        target_pattern = self.pattern_database.get(self.attack_type)
        if not target_pattern:
            print(f"{self.attack_type} not found in patterns")
            return False

        if re.search(target_pattern, user_input, re.IGNORECASE):
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "attacker_ip": request.remote_addr,
                "http_method": request.method,
                "attacker_port": request.environ.get('REMOTE_PORT'),
                "signature": f"Potential Web Injection ({self.attack_type})"
            }
        return False

    def check_delay(self):
        """Проверка на автоматизацию сканирования по таймингам между запросами"""
        current_time = time.time()
        attacker_ip = request.remote_addr

        if attacker_ip not in self.attacker_tracker:
            self.attacker_tracker[attacker_ip] = deque(maxlen=5)

        self.attacker_tracker[attacker_ip].append(current_time)
        methods_delay = list(self.attacker_tracker[attacker_ip])

        if len(methods_delay) > 1:
            last_delay = methods_delay[-1] - methods_delay[-2]
            if last_delay <= self.delay:
                return {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "attacker_ip": attacker_ip,
                    "http_method": request.method,
                    "attacker_port": request.environ.get('REMOTE_PORT'),
                    "signature": "High Rate Automation Scan / DDOS"
                }
        return False


class Low_Interaction_HoneyPot:
    def __init__(self, port: int, server_host: str = "0.0.0.0") -> None:
        self.port = port
        self.server_host = server_host
        self.is_running = True

    def start_loop(self):
        """Запуск бесконечного цикла прослушки сокета в фоновом режиме"""
        threading.Thread(target=self._listen_loop, daemon=True).start()
        print(f"Низкоуровневая ловушка успешно запущена на порту {self.port}")

    def _listen_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.server_host, self.port))
            s.listen(5)

            while self.is_running:
                try:
                    connection, client_addr = s.accept()
                    raw_data = connection.recv(1024).decode("utf-8", errors="ignore")

                    user_agent = "Unknown / Raw TCP Connection"
                    for line in raw_data.split("\n"):
                        if line.startswith("User-Agent:"):
                            user_agent = line.split("User-Agent:")[1].strip()

                    attack_info = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "attacker_ip": client_addr[0],
                        "attacker_port": client_addr[1],
                        "target_port": self.port,
                        "http_method": "GET" if "GET" in raw_data else "RAW_TCP",
                        "signature": "Potential Port Scan / Reconnaissance",
                        "user_agent": user_agent,
                        "honeypot_name": f"low_interaction_port_{self.port}",
                        "risk_lvl": 1,
                        "payload": raw_data.strip() if raw_data else "No payload"
                    }

                    try:
                        requests.post("http://center-backend:8000/api/v1/telemetry", json=attack_info, timeout=2)
                    except Exception as e:
                        print(f"Ошибка отправки сокет-лога: {e}")

                    connection.close()
                except Exception as e:
                    print(f"Ошибка сокета на порту {self.port}: {e}")
