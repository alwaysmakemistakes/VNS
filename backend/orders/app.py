from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from models import get_db_connection, create_orders_tables
from prometheus_flask_exporter import PrometheusMetrics
import pika, json


app = Flask(__name__)
metrics = PrometheusMetrics(app)
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
CORS(app)

create_orders_tables()

def publish_order(user, product_ids):
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="order_queue", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="order_queue",
        body=json.dumps({"user": user, "products": product_ids}),
        properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
    )
    connection.close()

@app.route("/cart", methods=["GET"])
@jwt_required()
def get_cart():
    user = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, product_id FROM cart WHERE username=%s", (user,))
    items = [{"id": row[0], "product_id": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(items)

@app.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():
    user = get_jwt_identity()
    data = request.get_json()
    product_id = data.get("product_id")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO cart (username, product_id) VALUES (%s, %s)", (user, product_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Added to cart"}), 201

@app.route("/cart/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(item_id):
    user = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id=%s AND username=%s", (item_id, user))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Removed from cart"})

@app.route("/orders/checkout", methods=["POST"])
@jwt_required()
def checkout():
    user = get_jwt_identity()
    data = request.get_json()
    items = data.get("items")

    if not items:
        return jsonify({"message": "No items provided"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    for item in items:
        product_id = item["id"]
        cur.execute(
            "INSERT INTO orders (username, product_id) VALUES (%s, %s)",
            (user, product_id)
        )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Order placed!"}), 201


@app.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    user = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, product_id, created_at FROM orders WHERE username=%s ORDER BY created_at DESC", (user,))
    orders = [{"id": row[0], "product_id": row[1], "created_at": row[2].isoformat()} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(orders)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
