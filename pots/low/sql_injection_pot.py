from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from app.logging import save_to_json_log
import re

app = FastAPI(title="SqlInjection Pot")

@app.get("/auth/login/")
async def login(username: str, password: str, request: Request):
    if re.findall(r'[\'"\s]+(or|and)\b', username):
        attack_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.client.host,
            'method': 'GET',
            'user_agent': request.headers.get('user-agent'),
            'pot_name': 'sql_injection_pot',
            'payload' : f"user={username}&pass={password}"
        }

        save_to_json_log(attack_info)

        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    return JSONResponse(status_code=200, content={"status": "ok"})