CREATE ROLE admin WITH LOGIN SUPERUSER;
CREATE DATABASE app_db OWNER admin;

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    category TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL,
    sold_quantity INTEGER NOT NULL DEFAULT 0
);


INSERT INTO products (name, price, category, available_quantity, sold_quantity) VALUES
('Book A', 19.99, 'Books', 50, 10),
('T-Shirt', 29.99, 'Clothing', 20, 5),
('QQ', 29.99, 'Clothing', 20, 5),
('Book B', 19.99, 'Books', 50, 10),
('WWt', 29.99, 'Clothing', 20, 5),
('EEE', 29.99, 'Clothing', 20, 5),
('Book C', 19.99, 'Books', 50, 10),
('BBB', 29.99, 'Clothing', 20, 5),
('AA', 29.99, 'Clothing', 20, 5),
('Headphones', 99.99, 'Electronics', 15, 3);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    product_id INTEGER NOT NULL,
    wallet_balance NUMERIC(12,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
