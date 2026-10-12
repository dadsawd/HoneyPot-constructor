import json
import os

def save_to_json_log(attack_info: dict):
    filename = "honey_pots.json"
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(attack_info)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)