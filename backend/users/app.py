from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from models import get_db_connection, create_users_table
from prometheus_flask_exporter import PrometheusMetrics
import hashlib
import requests

app = Flask(__name__)
metrics = PrometheusMetrics(app)
AUDIT_SERVICE_URL = "http://audit_service:5000/audit/event"
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret"  # замените на переменную окружения в проде
jwt = JWTManager(app)

create_users_table()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def audit_event(entity_type, entity_id, event_type, payload):
    try:
        requests.post(
            AUDIT_SERVICE_URL,
            json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "event_type": event_type,
                "payload": payload
            },
            timeout=2
        )
    except requests.RequestException as e:
        # Можно залогировать ошибку, чтобы не сломать основной сервис
        print(f"Audit error: {e}")

@app.route("/users/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    password_hash = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Используем RETURNING id, чтобы получить user_id
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        # Отправляем событие в Audit Service
        audit_event(
            entity_type="user",
            entity_id=user_id,
            event_type="user_created",
            payload={"username": username}
        )

    except Exception as e:
        return jsonify({"error": "User already exists"}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    password_hash = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE username = %s AND password = %s", (username, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        user_id = user[0]

        # Отправляем событие в Audit Service
        audit_event(
            entity_type="user",
            entity_id=user_id,
            event_type="user_login",
            payload={"username": username}
        )

        token = create_access_token(identity=username)
        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/users/me", methods=["GET"])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    return jsonify({"user": current_user})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
