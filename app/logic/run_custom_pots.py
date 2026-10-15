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

    config = json.loads(raw_config)
    # ИСПРАВЛЕНО: Корректный синтаксис получения порта из словаря
    my_port = int(config.get('port', 8000))

    print(f"[⚙️ CONTAINER] Сборка кастомного профиля: {config.get('pot_name')}")

    # ИСПРАВЛЕНО: Передаем в триггер ВСЕ необходимые аргументы по твоей ООП-структуре
    custom_trigger = Triggers(
        endpoint=config["url"],
        tries_to_login=int(config["tries_to_login"]),
        http_method="POST",
        attack_type=config["attack_type"],
        port=my_port
    )

    # Настраиваем имена полей ввода для формы лже-сайта
    custom_web = WebBase(
        url=config["url"],
        login_field=config["login_field"],
        password_field=config["password_field"]
    )

    # Собираем ловушку воедино
    pot = HoneyPot(
        port=my_port,
        pot_name=config["pot_name"],
        risk_lvl=int(config["risk_lvl"])
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

    print(f"[🚀 PROD ACTIVE] Ловушка открыта на внутреннем порту 8000 | Эндпоинт: {config['url']}")
    # Запускаем Flask на внутреннем порту 8000 контейнера (докер сам пробросит его наружу)
    app.run(host='0.0.0.0', port=8000)
