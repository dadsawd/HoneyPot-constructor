# run_custom_pots.py
import os
import json
from flask import Flask
# ИСПРАВЛЕНО: Импортируем твои ООП-классы из файла contructor.py
from contructor import HoneyPot, Triggers, WebBase

# ИСПРАВЛЕНО: Указываем правильную папку с фейк-шаблонами
app = Flask(__name__, template_folder='faketemplates')

if __name__ == '__main__':
    # ИСПРАВЛЕНО: Читаем точное имя переменной POT_CONFIG, которую шлет main.py
    raw_config = os.environ.get('POT_CONFIG')
    if not raw_config:
        print("Error, config not found in environment!")
        exit(1)

    # ИСПРАВЛЕНО: Защита от багов кавычек Windows (парсим и Base64, и обычную строку)
    try:
        config = json.loads(raw_config)
    except json.JSONDecodeError:
        import base64

        try:
            decoded_bytes = base64.b64decode(raw_config)
            config = json.loads(decoded_bytes.decode('utf-8'))
        except Exception as e:
            print(f"Critical JSON/Base64 decode error: {e}")
            exit(1)
    # ИСПРАВЛЕНО: Корректный синтаксис получения порта из словаря
    my_port = int(config.get('port', 8000))

    print(f"[⚙️ CONTAINER] Сборка кастомного профиля: {config.get('pot_name')}")

    # ИСПРАВЛЕНО: Передаем в триггер ВСЕ необходимые аргументы по твоей ООП-структуре
    custom_trigger = Triggers(
        endpoint=config.get("url"),
        tries_to_login=int(config.get("tries_to_login", 5)),
        http_method="POST",
        attack_type=config.get("attack_type"),
        port=my_port
    )

    # Настраиваем имена полей ввода для формы лже-сайта
    custom_web = WebBase(
        url=config.get("url"),
        login_field=config.get("login_field"),
        password_field=config.get("password_field")
    )

    # Собираем ловушку воедино
    pot = HoneyPot(
        port=my_port,
        pot_name=config.get("pot_name"),
        risk_lvl=int(config.get("risk_lvl", 2))
    )
    pot.trigger = custom_trigger
    pot.web = custom_web

    # Динамически регистрируем маршрут на Flask-сервере внутри контейнера
    app.add_url_rule(
        rule=pot.trigger.endpoint,
        endpoint=pot.pot_name,
        view_func=pot.handle_request,
        methods=["POST", "GET"]
    )

    print(f"[🚀 PROD ACTIVE] Ловушка открыта на внутреннем порту 8000 | Эндпоинт: {config.get('url')}")
    # Запускаем Flask на внутреннем порту 8000 контейнера (докер сам пробросит его наружу)
    app.run(host='0.0.0.0', port=8000)
