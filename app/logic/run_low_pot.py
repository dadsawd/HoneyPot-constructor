# app/logic/run_low_pot.py
import sys
import socket
import requests


def run_low_interaction_pot(port: int):
    # Создаем чистый TCP сокет хост-машины
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(('0.0.0.0', port))
        server.listen(5)
        print(f"[🛡️ LOW-POT ACTIVE] Низкоуровневый капкан запущен на порту {port}")
    except Exception as e:
        print(f"[❌ ERROR] Не удалось открыть порт {port}: {e}")
        sys.exit(1)

    while True:
        try:
            # Ждем пока хакер (или сканер nmap) постучится на этот порт
            client_socket, client_address = server.accept()
            attacker_ip = client_address[0]
            attacker_port = client_address[1]

            # Читаем сырой вредоносный пакет (брутфорс, сканирование сигнатур и т.д.)
            payload = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()

            # Красиво имитируем стандартный ответ закрытой промышленной службы (например, SSH или Телнет)
            client_socket.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n")
            client_socket.close()

            if payload:
                print(f"[💥 DETECT] Перехвачен сырой трафик с IP {attacker_ip}: {payload}")

                # Формируем Threat Intelligence лог под твой застрахованный main.py
                attack_info = {
                    "pot_name": f"low_pot_{port}",
                    "attacker_ip": attacker_ip,
                    "attacker_port": attacker_port,
                    "target_port": port,
                    "signature": "Low-Interaction Raw TCP Scan / Bruteforce",
                    "payload": payload,
                    "http_method": "RAW",
                    "user_agent": "Raw Socket Scanner"
                }

                # МГНОВЕННО СТРЕЛЯЕМ В ТВОЙ МЕЙН (так как скрипт на Windows, шлем на localhost)
                try:
                    requests.post("http://127.0.0", json=attack_info, timeout=2)
                except Exception as e:
                    print(f"Ошибка пуша в main.py: {e}")

        except KeyboardInterrupt:
            print("\nЛовушка остановлена.")
            break
        except Exception as e:
            print(f"Ошибка сессии: {e}")


if __name__ == '__main__':
    # Скрипт принимает номер порта третьим аргументом из вызова subprocess
    if len(sys.argv) > 1:
        target_port = int(sys.argv[1])
    else:
        target_port = 8022  # Дефолтный порт под фейковый SSH

    run_low_interaction_pot(target_port)
