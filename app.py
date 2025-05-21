from flask import Flask, jsonify, request 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Настройка подключения к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/mydb'

# Инициализация SQLAlchemy для работы с базой данных
db = SQLAlchemy(app)

# Определение модели данных
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable=True)

# Роут для главной страницы
@app.route("/")
def hello():
    return "Hello, Docker!"  # Простое сообщение для проверки работы приложения

# Роут для получения списка всех задач
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()

    # Преобразование списка задач в JSON-формат и возврат клиенту
    return jsonify([{'id': task.id, 'title': task.title, 'description': task.description} for task in tasks])

# Роут для добавления новой задачи
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json  # Получение данных из тела запроса в формате JSON
    # Создание новой задачи на основе полученных данных

    new_task = Task(title=data['title'], description=data.get('description', ''))
    db.session.add(new_task)  # Добавление задачи в сессию базы данных
    db.session.commit()  # Сохранение изменений в базе данных

    # Возврат данных новой задачи и статус-кода 201 (Created)
    return jsonify({'id': new_task.id, 'title': new_task.title, 'description': new_task.description}), 201

# Роут для удаления задачи по её ID
@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get_or_404(id)  # Поиск задачи по ID. Если задача не найдена, возвращается ошибка 404
    db.session.delete(task)  # Удаление задачи из базы данных
    db.session.commit()  # Сохранение изменений
    return '', 204

# Роут для проверки здоровья приложения
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Создание пустой БД
@app.before_request
def create_tables():
    db.create_all()

# Запуск приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание таблиц, если они отсутствуют
    app.run(host="0.0.0.0", port=5000)