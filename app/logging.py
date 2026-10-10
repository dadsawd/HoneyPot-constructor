import os
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
default_log_path = base_dir / "honey_pots.json"

def save_to_json_log(attack_info: dict, file_path: Path = default_log_path):

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(attack_info)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(attack_info, f, ensure_ascii=False, indent=4)