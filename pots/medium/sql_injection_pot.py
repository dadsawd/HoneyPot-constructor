from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
from datetime import datetime
from app.logging import save_to_json_log
from app.database.databaze import save_logs
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="SqlInjection Pot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

@app.post("/auth/login/")
@app.post("/auth/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if re.findall(r'[\'"\s]+(or|and)\b', username):
        attack_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.client.host,
            'method': 'POST',
            'user_agent': request.headers.get('user-agent'),
            'pot_name': 'sql_injection_pot',
            'payload' : f"user={username}&pass={password}"
        }

        save_to_json_log(attack_info)

        try:
            save_logs(attack_info)
        except Exception as e:
            print(f"Error: {e}")

        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    return JSONResponse(status_code=200, content={"status": "ok"})