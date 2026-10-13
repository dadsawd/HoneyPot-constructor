FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask flask-cors requests
COPY sql_injection_pot.py .
COPY FAKE_login.html ./templates/fake_login.html
EXPOSE 80
CMD ["python", "sql_injection_pot.py"]