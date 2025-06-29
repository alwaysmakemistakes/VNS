import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def create_products_table():
    conn = get_db_connection()
    cur = conn.cursor()

    # Создание таблиц
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            category TEXT NOT NULL,
            stock_quantity INTEGER NOT NULL,
            sold_quantity INTEGER NOT NULL DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS discounts (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            category VARCHAR(255),
            discount_percent NUMERIC(5,2) NOT NULL,
            expires_at TIMESTAMP NOT NULL
        );
    """)

    # Проверяем — есть ли уже товары?
    cur.execute("SELECT COUNT(*) FROM products;")
    count = cur.fetchone()[0]

    if count == 0:
        # Вставляем тестовые товары
        cur.execute("""
            INSERT INTO products (name, price, category, stock_quantity, sold_quantity)
            VALUES
            ('Smartphone', 500.00, 'electronics', 15, 8),
            ('Wireless Headphones', 150.00, 'electronics', 30, 12),
            ('Running Shoes', 90.00, 'sportswear', 20, 5),
            ('Laptop', 1200.00, 'electronics', 10, 3),
            ('Yoga Mat', 35.00, 'sportswear', 50, 25),
            ('Coffee Maker', 80.00, 'home_appliances', 18, 7),
            ('Smartwatch', 200.00, 'electronics', 12, 4),
            ('Backpack', 60.00, 'accessories', 40, 18),
            ('Blender', 45.00, 'home_appliances', 22, 10),
            ('Gaming Mouse', 70.00, 'electronics', 25, 9),
            ('Tablet', 300.00, 'electronics', 20, 6),
            ('Fitness Tracker', 99.00, 'electronics', 30, 15),
            ('Desk Lamp', 25.00, 'home_appliances', 40, 20),
            ('Action Camera', 250.00, 'electronics', 15, 8),
            ('Water Bottle', 12.00, 'accessories', 60, 30),
            ('Electric Kettle', 55.00, 'home_appliances', 18, 10),
            ('Sunglasses', 45.00, 'accessories', 25, 12),
            ('Bluetooth Speaker', 80.00, 'electronics', 35, 14),
            ('Hiking Boots', 120.00, 'sportswear', 20, 7),
            ('Wireless Charger', 35.00, 'electronics', 28, 10),
            ('Digital Camera', 450.00, 'electronics', 10, 4),
            ('Dress Shoes', 85.00, 'sportswear', 22, 9),
            ('Microwave Oven', 110.00, 'home_appliances', 12, 6),
            ('Power Bank', 40.00, 'electronics', 40, 16),
            ('Wallet', 30.00, 'accessories', 50, 22),
            ('Mechanical Keyboard', 90.00, 'electronics', 15, 5),
            ('Rice Cooker', 70.00, 'home_appliances', 14, 7),
            ('Hair Dryer', 45.00, 'home_appliances', 18, 9),
            ('Camping Tent', 150.00, 'sportswear', 10, 3),
            ('USB Flash Drive', 20.00, 'electronics', 100, 40),
            ('Winter Jacket', 200.00, 'sportswear', 12, 4),
            ('Electric Toothbrush', 60.00, 'home_appliances', 30, 14),
            ('Photo Printer', 140.00, 'electronics', 8, 2),
            ('Beach Towel', 25.00, 'accessories', 45, 20),
            ('Wireless Mouse', 25.00, 'electronics', 40, 18),
            ('Smart Light Bulb', 30.00, 'home_appliances', 25, 11);
        """)

        # Добавляем скидки на отдельные товары
        cur.execute("""
            INSERT INTO discounts (product_id, discount_percent, expires_at)
            VALUES
                (1, 20.00, NOW() + INTERVAL '10 days'),
                (2, 20.00, NOW() + INTERVAL '5 days'),
                (4, 20.00, NOW() + INTERVAL '7 days'),
                (6, 20.00, NOW() + INTERVAL '3 days'),
                (8, 20.00, NOW() + INTERVAL '4 days'),
                (10, 20.00, NOW() + INTERVAL '6 days');
        """)

        # Добавляем скидки на категории
        cur.execute("""
            INSERT INTO discounts (category, discount_percent, expires_at)
            VALUES
                ('home_appliances', 15.00, NOW() + INTERVAL '3 days');
        """)

        # Создание индекса для быстрого поиска по category
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products (category);
        """)

        # Создание индекса для быстрого поиска по name (ILIKE)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_name
            ON products (name text_pattern_ops);
        """)

        print("Test products and discounts inserted.")

    conn.commit()
    cur.close()
    conn.close()
