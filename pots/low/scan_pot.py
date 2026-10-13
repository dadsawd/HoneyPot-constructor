from datetime import datetime
from app.json_logging import save_to_json_log
import socket

server_address = ('127.0.0.1', 8080)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(server_address)
    s.listen(1)
    connection, client_address = s.accept()
    raw_data = connection.recv(1024).decode("utf-8", errors="ignore")
    user_agent = "Unknown / Raw TCP Connection"
    for line in raw_data.split("\n"):
        if line.startswith("User-Agent:"):
            user_agent = line.split("User-Agent:")[1].strip()
    try:
        attack_info = {
            "timestamp": datetime.now().isoformat(),
            "attacker_ip" : client_address[0],
            "http_method" : "GET",
            "signature" : "Potential Web Scan / Reconnaissance",
            "attacker_port" : client_address[1],
            "user_agent" : user_agent,
            "target_port" : s.getsockname()[1],
            "pot_name": "Spider/Crawler pot"
        }
    finally:
        connection.close()
    save_to_json_log(attack_info)