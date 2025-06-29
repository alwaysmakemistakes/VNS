from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from models import get_db_connection, create_orders_tables
from prometheus_flask_exporter import PrometheusMetrics
from decimal import Decimal, ROUND_HALF_UP
import pika
import json
import requests
import datetime

app = Flask(__name__)
metrics = PrometheusMetrics(app)
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
CORS(app)

create_orders_tables()

USERS_SERVICE_URL = "http://users1:5000/users/wallet/charge"


def publish_order(user, product_ids):
    rabbitmq_urls = [
        "amqp://guest:guest@rabbitmq1:5672/%2F",
        "amqp://guest:guest@rabbitmq2:5672/%2F",
        "amqp://guest:guest@rabbitmq3:5672/%2F"
    ]

    connection = None
    for url in rabbitmq_urls:
        try:
            parameters = pika.URLParameters(url)
            connection = pika.BlockingConnection(parameters)
            print(f"[✓] Connected to RabbitMQ at {url}")
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"[!] Could not connect to {url}. Trying next node...")
    else:
        print("[✗] All RabbitMQ nodes unreachable. Order not published.")
        return

    channel = connection.channel()
    channel.queue_declare(queue="order_queue", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="order_queue",
        body=json.dumps({
            "username": user,
            "product_ids": product_ids
        }),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"[✓] Order published for {user}")
    connection.close()


def get_discounted_price(cur, product_id, category, original_price):
    """
    Возвращает цену товара с учетом возможной скидки.
    """
    now = datetime.datetime.utcnow()

    discount_percent = Decimal("0")

    # Проверка скидки на продукт
    cur.execute("""
        SELECT discount_percent
        FROM discounts
        WHERE product_id = %s
          AND expires_at > %s
        ORDER BY expires_at DESC
        LIMIT 1;
    """, (product_id, now))
    row = cur.fetchone()
    if row:
        discount_percent = Decimal(row[0])
    else:
        # Проверяем скидку на категорию
        cur.execute("""
            SELECT discount_percent
            FROM discounts
            WHERE category = %s
              AND expires_at > %s
            ORDER BY expires_at DESC
            LIMIT 1;
        """, (category, now))
        row = cur.fetchone()
        if row:
            discount_percent = Decimal(row[0])

    discount_factor = Decimal("1") - (discount_percent / Decimal("100"))
    discounted_price = Decimal(original_price) * discount_factor
    return float(round(discounted_price, 2))


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
    cur.execute(
        "INSERT INTO cart (username, product_id) VALUES (%s, %s)",
        (user, product_id)
    )
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
    cur.execute(
        "DELETE FROM cart WHERE id=%s AND username=%s",
        (item_id, user)
    )
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

    total_price = Decimal("0.0")

    for item in items:
        product_id = item["id"]
        quantity = item.get("quantity", 1)

        # получаем цену и категорию товара
        cur.execute("""
            SELECT stock_quantity, price, category
            FROM products
            WHERE id = %s
        """, (product_id,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": f"Product {product_id} not found"}), 404

        stock_quantity, price, category = row

        if stock_quantity < quantity:
            cur.close()
            conn.close()
            return jsonify({
                "error": f"Not enough stock for product {product_id}. Available: {stock_quantity}"
            }), 400

        final_price = Decimal(get_discounted_price(cur, product_id, category, price))
        total_price += final_price * Decimal(quantity)

    total_price_float = float(total_price)

    try:
        response = requests.post(
            USERS_SERVICE_URL,
            json={"amount": total_price_float},
            headers={
                "Authorization": f"Bearer {request.headers.get('Authorization').split()[-1]}"
            },
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Payment failed",
                "details": response.json()
            }), 400

    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to reach wallet service",
            "details": str(e)
        }), 500

    for item in items:
        product_id = item["id"]
        quantity = item.get("quantity", 1)

        cur.execute(
            "INSERT INTO orders (username, product_id) VALUES (%s, %s)",
            (user, product_id)
        )
        cur.execute("""
            UPDATE products
            SET stock_quantity = stock_quantity - %s,
                sold_quantity = sold_quantity + %s
            WHERE id = %s
        """, (quantity, quantity, product_id))

    cur.execute("DELETE FROM cart WHERE username = %s", (user,))
    conn.commit()
    cur.close()
    conn.close()

    publish_order(user, [item["id"] for item in items])

    return jsonify({"message": "Order placed!"}), 201


@app.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    user = get_jwt_identity()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, product_id, created_at
        FROM orders
        WHERE username=%s
        ORDER BY created_at DESC
    """, (user,))
    orders = [
        {
            "id": row[0],
            "product_id": row[1],
            "created_at": row[2].isoformat()
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(orders)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
