from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@app.route("/products", strict_slashes=False)
def get_all_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM products;")
    products = [{"id": row[0], "name": row[1], "price": float(row[2])} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(products)

@app.route("/products/<int:product_id>", strict_slashes=False)
def get_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM products WHERE id = %s;", (product_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({"id": row[0], "name": row[1], "price": float(row[2])})
    else:
        return jsonify({"error": "Product not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
