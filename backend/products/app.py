from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from models import get_db_connection, create_products_table
from decimal import Decimal, ROUND_HALF_UP
import datetime
import math

app = Flask(__name__)
metrics = PrometheusMetrics(app)

create_products_table()

def get_discounted_price(cur, product_id, category, original_price):
    now = datetime.datetime.utcnow()

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
        factor = Decimal("1.0") - (discount_percent / Decimal("100"))
        final_price = (Decimal(original_price) * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(final_price)

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
        factor = Decimal("1.0") - (discount_percent / Decimal("100"))
        final_price = (Decimal(original_price) * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(final_price)

    return float(original_price)


@app.route("/products", strict_slashes=False)
def get_all_products():
    page = int(request.args.get("page", 1))
    print(">>> page =", page)
    per_page = 8

    conn = get_db_connection()
    cur = conn.cursor()

    # Считаем общее количество товаров
    cur.execute("SELECT COUNT(*) FROM products;")
    total_items = cur.fetchone()[0]
    total_pages = max(1, math.ceil(total_items / per_page))

    offset = (page - 1) * per_page
    cur.execute("""
        SELECT id, name, price, category, stock_quantity, sold_quantity
        FROM products
        ORDER BY id
        LIMIT %s OFFSET %s;
    """, (per_page, offset))

    products = []
    for row in cur.fetchall():
        product_id, name, price, category, stock_qty, sold_qty = row
        final_price = get_discounted_price(cur, product_id, category, price)
        products.append({
            "id": product_id,
            "name": name,
            "price": final_price,
            "original_price": float(price),
            "category": category,
            "stock_quantity": stock_qty,
            "sold_quantity": sold_qty
        })

    # Формируем список страниц для отображения (максимум 5 кнопок)
    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)
    pages = list(range(start_page, end_page + 1))

    result = {
        "products": products,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "pages": pages
        }
    }

    cur.close()
    conn.close()
    return jsonify(result)


@app.route("/products/<int:product_id>", strict_slashes=False)
def get_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, price, category, stock_quantity, sold_quantity
        FROM products
        WHERE id = %s;
    """, (product_id,))
    row = cur.fetchone()

    if row:
        product_id, name, price, category, stock_qty, sold_qty = row
        final_price = get_discounted_price(cur, product_id, category, price)
        result = {
            "id": product_id,
            "name": name,
            "price": final_price,
            "original_price": float(price),
            "category": category,
            "stock_quantity": stock_qty,
            "sold_quantity": sold_qty
        }
        cur.close()
        conn.close()
        return jsonify(result)
    else:
        cur.close()
        conn.close()
        return jsonify({"error": "Product not found"}), 404

@app.route("/products/search", strict_slashes=False)
def search_products():
    query = request.args.get("query", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 8

    conn = get_db_connection()
    cur = conn.cursor()

    if not query:
        cur.close()
        conn.close()
        return jsonify({
            "products": [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "total_items": 0,
                "pages": []
            }
        })

    # Считаем количество найденных товаров
    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE name ILIKE %s
           OR category ILIKE %s;
    """, (f"%{query}%", f"%{query}%"))
    total_items = cur.fetchone()[0]
    total_pages = max(1, math.ceil(total_items / per_page))
    offset = (page - 1) * per_page

    cur.execute("""
        SELECT id, name, price, category, stock_quantity, sold_quantity
        FROM products
        WHERE name ILIKE %s
           OR category ILIKE %s
        ORDER BY id
        LIMIT %s OFFSET %s;
    """, (f"%{query}%", f"%{query}%", per_page, offset))

    products = []
    for row in cur.fetchall():
        product_id, name, price, category, stock_qty, sold_qty = row
        final_price = get_discounted_price(cur, product_id, category, price)
        products.append({
            "id": product_id,
            "name": name,
            "price": final_price,
            "original_price": float(price),
            "category": category,
            "stock_quantity": stock_qty,
            "sold_quantity": sold_qty
        })

    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)
    pages = list(range(start_page, end_page + 1))

    result = {
        "products": products,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "pages": pages
        }
    }

    cur.close()
    conn.close()
    return jsonify(result)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
