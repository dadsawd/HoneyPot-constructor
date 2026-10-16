# universal_pot/run_pot.py (или твой файл классов конструктора)
from datetime import datetime
from flask import Flask, request, render_template_string
from collections import deque
import re
import socket
import threading
import time
import requests
import os
import json
import urllib.parse

app = Flask(__name__)

class HoneyPot:
    def __init__(self, port: int, pot_name: str, risk_lvl: int) -> None:
        self.port = port
        self.pot_name = pot_name
        self.risk_lvl = risk_lvl
        self.trigger = None
        self.web = None

    def send_telemetry(self, attack_info: dict) -> None:
        """Метод отправки лога в Центральный бэкенд на хост-компьютер через докер-мост"""
        attack_info["honeypot_name"] = self.pot_name
        attack_info["target_port"] = self.port
        attack_info["risk_lvl"] = self.risk_lvl

        print(f"[🚨 ДЕТЕКТ] Ловушка {self.pot_name} зафиксировала атаку!")

        try:
            # host.docker.internal выводит сетевой запрос из контейнера прямо на порт 8000 твоего ПК
            requests.post("http://192.168.3.86:8000/api/v1/telemetry", json=attack_info, timeout=2)
        except Exception as e:
            print(f"Ошибка отправки телеметрии: {e}")

    def handle_request(self):
        """Главный диспетчер запросов ловушки среднего уровня взаимодействия"""
        # Защита от WAF Bypass: собираем и декодируем весь трафик (GET и POST)
        get_data = " ".join([f"{k}={v}" for k, v in request.args.items()])
        post_data = " ".join([f"{k}={v}" for k, v in request.form.items()])
        combined_input = urllib.parse.unquote(f"{get_data} {post_data}").strip()

        # 1. Проверяем триггер на задержку (Брутфорс автоматизацией)
        attack = self.trigger.check_delay()

        # 2. Проверяем триггер на инъекции во всем входящем потоке
        if not attack and combined_input:
            attack = self.trigger.check_input(combined_input)

        # 3. Если это обычный перебор формы, проверяем счетчик попыток входа
        if not attack and request.method == "POST":
            attack = self.trigger.check_tries_to_log()

        # Если капкан сработал — шлем телеметрию и подыгрываем хакеру
        if attack and isinstance(attack, dict):
            attack["user_agent"] = request.headers.get("user-agent", "unknown")
            attack["payload"] = combined_input if combined_input else "No Input Data"
            self.send_telemetry(attack)

            # Психологический капкан для SQLi: отдаем структурированный фейковый слив
            if self.trigger.attack_type == 'SQL-injection':
                return {
                    "status": "success",
                    "data": [
                        {"id": 1, "user": "admin", "password_hash": "$2b$12$HoneyForgeSecretKeyAdminHash"},
                        {"id": 2, "user": "flag_user_dgtu", "password_hash": "$2b$12$FakeDataForScepticPentester"}
                    ]
                }, 200

            # Психологический капкан для XSS: имитируем успешное исполнение кода
            if self.trigger.attack_type == 'XSS-injection':
                return "<html><body><h1>Search Results</h1><script>console.log('XSS Executed');</script></body></html>", 200

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
        self.counter += 1
        if self.counter >= self.tries_to_login:
            print(f"Превышено количество попыток входа: {self.endpoint}, запрос № {self.counter}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "attacker_ip": request.remote_addr,
                "http_method": request.method,
                "attacker_port": request.environ.get('REMOTE_PORT', 0),
                "signature": "Brute Force Attempt"
            }
        return False

    def check_input(self, user_input: str):
        if not self.attack_type:
            return False

        match_data = self.pattern_database.get(self.attack_type)
        if not match_data:
            print(f"{self.attack_type} not found in patterns")
            return False

        regex_pattern, official_signature = match_data

        if re.search(regex_pattern, user_input, re.IGNORECASE):
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "attacker_ip": request.remote_addr,
                "http_method": request.method,
                "attacker_port": request.environ.get('REMOTE_PORT', 0),
                "signature": official_signature
            }
        return False

    def check_delay(self):
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
                    "attacker_port": request.environ.get('REMOTE_PORT', 0),
                    "signature": "High Rate Automation Scan / DDOS"
                }
        return False

# Инициализация ловушки на основе JSON из переменной окружения Docker
if __name__ == "__main__":
    raw_config = os.environ.get("POT_CONFIG")
    if raw_config:
        config = json.loads(raw_config)
        my_port = int(config.get("port", 8000))

        custom_trigger = Triggers(
            endpoint=config["url"], tries_to_login=config["tries_to_login"],
            http_method="POST", attack_type=config["attack_type"], port=my_port
        )
        custom_web = WebBase(
            url=config["url"], login_field=config["login_field"], password_field=config["password_field"]
        )
        pot = HoneyPot(port=my_port, pot_name=config["pot_name"], risk_lvl=config["risk_lvl"])
        pot.trigger = custom_trigger
        pot.web = custom_web

        app.add_url_rule(
            rule=pot.trigger.endpoint, endpoint=pot.pot_name,
            view_func=pot.handle_request, methods=["POST", "GET"]
        )
        print(f"[🔥 ENGINE] Ловушка {pot.pot_name} успешно развернута на внутреннем порту 8000")
        app.run(host="0.0.0.0", port=8000)
