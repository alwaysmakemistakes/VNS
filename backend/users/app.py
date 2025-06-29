from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_cors import CORS
from models import get_db_connection, create_users_table
from prometheus_flask_exporter import PrometheusMetrics
import hashlib
import requests

app = Flask(__name__)
metrics = PrometheusMetrics(app)
AUDIT_SERVICE_URL = "http://audit_service:5000/audit/event"
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret"  # замените на env в проде
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
        print(f"Audit error: {e}")

@app.route("/users/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    wallet_balance = data.get("wallet_balance", 0.0)

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    password_hash = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (username, password, wallet_balance)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (username, password_hash, wallet_balance)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        audit_event(
            entity_type="user",
            entity_id=user_id,
            event_type="user_created",
            payload={
                "username": username,
                "wallet_balance": float(wallet_balance)
            }
        )
    except Exception as e:
        conn.rollback()
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
    cur.execute("""
        SELECT id, username, wallet_balance
        FROM users
        WHERE username = %s AND password = %s
    """, (username, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        user_id, username, wallet_balance = user

        audit_event(
            entity_type="user",
            entity_id=user_id,
            event_type="user_login",
            payload={"username": username}
        )

        token = create_access_token(identity=username)

        return jsonify({
            "token": token,
            "wallet_balance": float(wallet_balance)
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/users/me", methods=["GET"])
@jwt_required()
def me():
    current_user = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, wallet_balance
        FROM users
        WHERE username = %s
    """, (current_user,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        user_id, username, wallet_balance = user
        return jsonify({
            "id": user_id,
            "username": username,
            "wallet_balance": float(wallet_balance)
        })
    else:
        return jsonify({"error": "User not found"}), 404

@app.route("/users/wallet/topup", methods=["POST"])
@jwt_required()
def wallet_topup():
    current_user = get_jwt_identity()
    data = request.get_json()
    amount = data.get("amount")

    if amount is None or amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET wallet_balance = wallet_balance + %s
        WHERE username = %s
        RETURNING wallet_balance
    """, (amount, current_user))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if result:
        new_balance = float(result[0])

        audit_event(
            entity_type="user",
            entity_id=None,
            event_type="wallet_topup",
            payload={
                "username": current_user,
                "amount": amount,
                "new_balance": new_balance
            }
        )

        return jsonify({
            "message": f"Wallet topped up by {amount}",
            "wallet_balance": new_balance
        })
    else:
        return jsonify({"error": "User not found"}), 404

@app.route("/users/wallet/charge", methods=["POST"])
@jwt_required()
def wallet_charge():
    current_user = get_jwt_identity()
    data = request.get_json()
    amount = data.get("amount")

    if amount is None or amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT wallet_balance FROM users
        WHERE username = %s
    """, (current_user,))
    result = cur.fetchone()

    if not result:
        cur.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    current_balance = float(result[0])

    if current_balance < amount:
        cur.close()
        conn.close()
        return jsonify({"error": "Insufficient funds"}), 400

    cur.execute("""
        UPDATE users
        SET wallet_balance = wallet_balance - %s
        WHERE username = %s
        RETURNING wallet_balance
    """, (amount, current_user))
    new_balance = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    audit_event(
        entity_type="user",
        entity_id=None,
        event_type="wallet_charge",
        payload={
            "username": current_user,
            "amount": float(amount),
            "new_balance": float(new_balance)
        }
    )

    return jsonify({"wallet_balance": new_balance})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
