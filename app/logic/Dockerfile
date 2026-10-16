FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir flask requests
# Копируем файлы движка и запускатора строго под их реальными именами
COPY contructor.py .
COPY run_custom_pots.py .

# ИСПРАВЛЕНО: Вызываем тот файл, который реально скопировали выше
CMD ["python", "run_custom_pots.py"]
