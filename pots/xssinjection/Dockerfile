FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask flask-cors requests
COPY xss_injection_pot.py .
COPY comment_trap.html ./templates/comment_trap.html
EXPOSE 80
CMD ["python", "xss_injection_pot.py"]