import os
import json
from flask import Flask
from contructor import HoneyPot, Triggers, WebBase

app = Flask(__name__, templates_folder='faketemplates')

if __name__ == '__main__':
    raw_config = os.environ.get('CONFIG')
    if not raw_config:
        print("Error, config not found")
        exit(1)

    config = json.loads(raw_config)
    my_port = int(config['port', 8000])

    custom_trigger = Triggers(
        enpoint=config["url"],
        tries_to_login=config["tries_to_login"],

    )