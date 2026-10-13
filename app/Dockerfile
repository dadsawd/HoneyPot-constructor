FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask flask-cors "psycopg[binary]"
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]