import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def create_orders_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    # Создаем таблицу orders, если не существует
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        product_id INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

