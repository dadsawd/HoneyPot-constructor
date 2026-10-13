import psycopg
import json
import os

# Берем строку подключения из окружения, настроенного в docker-compose
db_url = os.getenv("DB_URL")


def init_db():
    with psycopg.connect(db_url) as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        pot_name VARCHAR(50) NOT NULL,
        attacker_ip INET NOT NULL,
        attacker_port INTEGER NULL,
        target_port INTEGER NULL,
        http_method VARCHAR(10) NULL,
        user_agent TEXT NULL,
        payload TEXT NULL
        )""")
        conn.commit()


def save_logs(pot_logs: dict):
    payload_data = pot_logs.get("payload")
    if isinstance(payload_data, dict):
        payload_data = json.dumps(payload_data, ensure_ascii=False)

    sql = """INSERT INTO logs (
    timestamp, pot_name, attacker_ip, attacker_port,
     target_port, http_method, user_agent, payload
     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    data_tuple = (
        pot_logs.get("timestamp"),
        pot_logs.get("pot_name"),
        pot_logs.get("ip"),
        pot_logs.get("attacker_port"),
        pot_logs.get("target_port"),
        pot_logs.get("method"),
        pot_logs.get("user_agent"),
        payload_data
    )

    with psycopg.connect(db_url) as conn:
        cur = conn.cursor()
        cur.execute(sql, data_tuple)
        conn.commit()


if __name__ == "__main__":
    init_db()