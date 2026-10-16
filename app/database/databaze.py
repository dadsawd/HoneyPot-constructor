import psycopg
import json
import os

db_url = os.environ.get("DB_URL") or "postgresql://user:password@localhost:5432/honeypot_db"


def init_db():
    with psycopg.connect(db_url) as conn:
        cur = conn.cursor()
        # ИСПРАВЛЕНО: Добавлена колонка signature и http_method для полной синхронизации
        cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        pot_name VARCHAR(50) NOT NULL,
        attacker_ip INET NOT NULL,
        attacker_port INTEGER NULL,
        target_port INTEGER NULL,
        http_method VARCHAR(10) NULL,
        signature VARCHAR(100) NULL,
        user_agent TEXT NULL,
        payload TEXT NULL
        )""")
        conn.commit()


def save_logs(pot_logs: dict):
    try:
        init_db()
    except Exception as e:
        print(f"Database init lazy error: {e}")

    pot_name = pot_logs.get("pot_name") or pot_logs.get("honeypot_name") or "test_trap"
    attacker_ip = pot_logs.get("attacker_ip") or pot_logs.get("attack_ip") or pot_logs.get("ip") or "127.0.0.1"

    # Собираем все поля для вставки
    signature = pot_logs.get("signature") or "Potential SQL-Injection Attempt"
    payload = pot_logs.get("payload") or "No Payload"
    target_port = int(pot_logs.get("target_port") or 8085)
    attacker_port = int(pot_logs.get("attacker_port") or 0)
    user_agent = pot_logs.get("user_agent") or "Unknown"
    http_method = pot_logs.get("http_method") or "POST"

    # ИСПРАВЛЕНО: Порядок колонок строго соответствует структуре таблицы и переменным ниже!
    query = """
       INSERT INTO logs (timestamp, pot_name, attacker_ip, attacker_port, target_port, http_method, signature, user_agent, payload)
       VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
       """

    with psycopg.connect(db_url) as conn:
        cur = conn.cursor()
        # ИСПРАВЛЕНО: Корректный кортеж аргументов для execute
        cur.execute(query,
                    (pot_name, attacker_ip, attacker_port, target_port, http_method, signature, user_agent, payload))
        conn.commit()


if __name__ == "__main__":
    init_db()
