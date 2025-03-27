from flask import Flask, jsonify, request 
from flask_sqlalchemy import SQLAlchemy
import random
import os
import time
import sys
from sqlalchemy import text

app = Flask(__name__)

# Настройка подключения к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/mydb')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 60,
}

# Инициализация SQLAlchemy для работы с базой данных
db = SQLAlchemy(app)
port = int(os.getenv("PORT", 5000))

# Определение модели данных
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable=True)

def wait_for_db():
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
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
                sys.exit(1)
    return False

# Роут для главной страницы
@app.route("/")
def hello():
    return f"Backend on port {port}"

# Роут для получения статуса сервиса
@app.route("/status")
def status():
    return {"service": "backend", "port": port}

# Роут для получения случайного числа
@app.route("/data")
def data():
    return {"value": random.randint(1, 100)}

# Роут для получения списка всех задач
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{'id': task.id, 'title': task.title, 'description': task.description} for task in tasks])

# Роут для добавления новой задачи
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    new_task = Task(title=data['title'], description=data.get('description', ''))
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'id': new_task.id, 'title': new_task.title, 'description': new_task.description}), 201

# Роут для удаления задачи по её ID
@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

# Роут для проверки здоровья приложения
@app.route('/health', methods=['GET'])
def health_check():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'status': 'healthy', 'db': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'db': 'disconnected', 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        print("Waiting for database to be ready...")
        wait_for_db()
        print("Creating database tables...")
        db.create_all()
    app.run(host="0.0.0.0", port=port)
