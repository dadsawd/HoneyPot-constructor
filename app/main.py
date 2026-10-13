from flask import Flask, render_template, request
from app.logging import save_to_json_log
from app.database import databaze

app = Flask(__name__)

@app.route('/')
def index():
    databaze.init_db()
    return render_template("UI.html")

@app.route('/api/v1/telemetry', methods=['POST'])
def collect_telemetry():
    save_to_json_log(attack_info=request.json)
    databaze.save_logs(pot_logs=request.json)