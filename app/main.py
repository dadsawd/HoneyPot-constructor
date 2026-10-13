from flask import Flask, render_template, request
from json_logging import save_to_json_log
from database import databaze

app = Flask(__name__)

@app.route('/')
def index():
    databaze.init_db()
    return render_template("UI.html")

@app.route('/api/v1/telemetry', methods=['POST'])
def collect_telemetry() -> None:
    save_to_json_log(attack_info=request.json)
    databaze.save_logs(pot_logs=request.json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
