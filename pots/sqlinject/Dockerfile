FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask flask-cors requests
COPY pots/sqlinject/sql_injection_pot.py .
COPY app/faketemplates/FAKE_login.html ./templates/fake_login.html
EXPOSE 80
CMD ["python", "sql_injection_pot.py"]