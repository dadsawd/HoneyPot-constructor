FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFERED=1
RUN pip install --no-cache-dir flask requests
COPY contructor.py .
COPY run_custom_pots.py .

CMD ["python", "run_pot.py"]