import os
import json
import subprocess

# Автоматически находим абсолютный путь к твоей папке faketemplates в структуре проекта
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Папка backend-features
APP_DIR = os.path.dirname(CURRENT_DIR)                   # Папка app
FAKETEMPLATES_DIR = os.path.join(APP_DIR, "faketemplates") # Папка faketemplates

def deploy_custom_honeypot(config_from_site: dict):
    port = config_from_site["port"]
    attack_type = config_from_site.get("attack_type")
    container_name = f"custom_pot_{port}"
    config_string = json.dumps(config_from_site)

    if attack_type in ['SQL-injection', 'XSS-injection']:
        # Веб-ловушка среднего взаимодействия (Medium)
        docker_command = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:8000",
            # Монтируем твою конкретную папку app/faketemplates внутрь контейнера
            "-v", f"{FAKETEMPLATES_DIR}:/app/templates:ro",
            "-e", f"POT_CONFIG={config_string}",
            "--network", "honeynet",
            "universal-pot-image:latest"
        ]
    else:
        # Сокет-ловушка низкого взаимодействия (Low)
        docker_command = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:{port}",
            "-e", f"POT_CONFIG={config_string}",
            "--network", "honeynet",
            "universal-socket-image:latest"
        ]

    try:
        # Гарантированно сносим старый контейнер на этом порту, если он мешает
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        # Запускаем новый кастомный капкан
        subprocess.run(docker_command, check=True)
        print(f"[🔥 GEN] Ловушка {container_name} успешно развернута на порту {port}!")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка Docker при деплое: {e}")
        return False
