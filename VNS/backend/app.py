from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import random
import os
import time
import sys
from sqlalchemy import text, inspect

app = Flask(__name__)

# Настройка подключения к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/mydb')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 60,
}

# Инициализация SQLAlchemy
db = SQLAlchemy(app)
port = int(os.getenv("PORT", 5000))

# Модель данных
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable=True)

def wait_for_db():
    """Ожидание готовности базы данных"""
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            with app.app_context():  # Добавляем контекст приложения
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            print("Database is available!")
            return True
        except Exception as e:
            print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Exiting...")
                return False
    return False

def create_tables_if_needed():
    """Создание таблиц, если они не существуют"""
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table('task'):
            print("Creating database tables...")
            db.create_all()
        else:
            print("Tables already exist, skipping creation")

# Эндпоинты
@app.route("/")
def home():
    return f"Backend service running on port {port}"

@app.route("/status")
def status():
    return {"service": "backend", "port": port, "status": "running"}

@app.route("/data")
def data():
    return {"value": random.randint(1, 100)}

@app.route('/tasks', methods=['GET'])
def get_tasks():
    with app.app_context():
        tasks = Task.query.all()
        return jsonify([{'id': task.id, 'title': task.title, 'description': task.description} for task in tasks])

@app.route('/tasks', methods=['POST'])
def add_task():
    with app.app_context():
        data = request.json
        new_task = Task(title=data['title'], description=data.get('description', ''))
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'id': new_task.id, 'title': new_task.title, 'description': new_task.description}), 201

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    with app.app_context():
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        return '', 204

@app.route('/health')
def health_check():
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "db": "connected",
            "service": f"backend:{port}"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "db": "disconnected",
            "error": str(e),
            "service": f"backend:{port}"
        }), 500

def initialize_app():
    """Инициализация приложения"""
    print(f"Starting backend service on port {port}")
    if not wait_for_db():
        sys.exit(1)
    
    # Создаем таблицы только если установлен флаг CREATE_TABLES
    if os.getenv('CREATE_TABLES', 'false').lower() == 'true':
        create_tables_if_needed()
    else:
        print("Skipping table creation (CREATE_TABLES not set)")

if __name__ == '__main__':
    initialize_app()
    app.run(host="0.0.0.0", port=port)