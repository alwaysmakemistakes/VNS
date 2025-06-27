from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@app.route("/products")
def get_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, price FROM products;")
    products = [{"name": row[0], "price": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(products)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
