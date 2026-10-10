from datetime import datetime
from pydantic import BaseModel, Field #перепиши как ООП
import json #pапихни в докер
import socket

server_address = ('127.0.0.1', 8080)

class AttackLogs(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    attacker_ip: str
    http_method: str
    user_agent: str
    signature: str = "Web Scan"
    attacker_port: int
    target_port: int


def save_to_file(log_obj: AttackLogs):
    try:
        with open("honeypot_logs.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_obj.model_dump(mode="json"))

    with open("honeypot_logs.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

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
        log_entry = AttackLogs(
            attacker_ip = client_address[0],
            http_method = "GET",
            signature = "Potential Web Scan / Reconnaissance",
            attacker_port = client_address[1],
            user_agent = user_agent if user_agent else "Unknown",
            target_port = s.getsockname()[1]
        )
    finally:
        connection.close()
    save_to_file(log_entry)

