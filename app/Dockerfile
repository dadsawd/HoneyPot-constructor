FROM python:3.11-slim
WORKDIR /app
COPY . /app
#ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir requests flask
    #flask-cors "psycopg[binary]"

#EXPOSE 8000
CMD ["python", "contructor.py"]