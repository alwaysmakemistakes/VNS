FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# По умолчанию запускаем app.py, но это можно переопределить через docker-compose
CMD ["python", "app.py"]
