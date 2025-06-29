import requests
import random
import time
import os
import urllib.parse

BASE_URL = os.getenv("BASE_URL", "http://nginx")

USERNAME = f"botuser_{random.randint(1000, 9999)}"
PASSWORD = "botpassword"
TOKEN = None

def register():
    payload = {"username": USERNAME, "password": PASSWORD}
    res = requests.post(f"{BASE_URL}/users/register", json=payload)
    if res.ok:
        print(f"[BOT] Registered new user {USERNAME}")
    else:
        print(f"[BOT] User may exist already: {res.status_code} {res.text}")

def login():
    global TOKEN
    payload = {"username": USERNAME, "password": PASSWORD}
    res = requests.post(f"{BASE_URL}/users/login", json=payload)
    TOKEN = res.json().get("token")
    if TOKEN:
        print(f"[BOT] Logged in as {USERNAME}")
    else:
        print(f"[BOT] Login failed: {res.text}")

def get_products():
    res = requests.get(f"{BASE_URL}/products/")
    try:
        data = res.json()
        if isinstance(data, dict) and "products" in data:
            return data["products"]
        elif isinstance(data, list):
            return data
        else:
            print(f"[BOT] Unexpected response format: {data}")
            return []
    except Exception as e:
        print(f"[BOT] Failed to parse products JSON: {e}")
        return []

def search_products(query):
    encoded_query = urllib.parse.quote_plus(query)
    url = f"{BASE_URL}/products/search?q={encoded_query}"
    try:
        res = requests.get(url)
        data = res.json()
        if isinstance(data, dict) and "products" in data:
            return data["products"]
        elif isinstance(data, list):
            return data
        else:
            print(f"[BOT] Unexpected search response: {data}")
            return []
    except Exception as e:
        print(f"[BOT] Search request failed: {e}")
        return []

def get_wallet():
    res = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    return res.json()["wallet_balance"]

def top_up(amount):
    res = requests.post(
        f"{BASE_URL}/users/wallet/topup",
        json={"amount": amount},
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    if res.ok:
        print(f"[BOT] Wallet topped up by ${amount}")
    else:
        print(f"[BOT] Top up failed: {res.status_code} {res.text}")

def add_to_cart(product_id):
    res = requests.post(
        f"{BASE_URL}/cart",
        json={"product_id": product_id},
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    if res.ok:
        print(f"[BOT] Added product {product_id} to cart.")
    else:
        print(f"[BOT] Failed to add to cart: {res.status_code} {res.text}")

def checkout(items):
    res = requests.post(
        f"{BASE_URL}/orders/checkout",
        json={"items": items},
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    if res.status_code == 201:
        print(f"[BOT] Order placed successfully.")
    else:
        print(f"[BOT] Checkout error: {res.status_code} {res.text}")

def run_bot():
    register()
    login()

    while True:
        # Пробуем сначала искать товар
        query = random.choice(["phone", "Laptop", "Coffee", "Yoga", "Headphones"])
        products = search_products(query)
        
        if products:
            print(f"[BOT] Found {len(products)} products for search '{query}'")
        else:
            print(f"[BOT] No products found for search '{query}', falling back to all products.")
            products = get_products()
            if not products:
                print("[BOT] No products found at all.")
                time.sleep(10)
                continue

        product = random.choice(products)
        product_id = product["id"]
        price = product["price"]

        balance = get_wallet()
        if balance < price:
            top_up(price - balance + 10)

        add_to_cart(product_id)

        items = [{"id": product_id, "quantity": 1}]
        checkout(items)

        wait_time = random.randint(30, 60)
        print(f"[BOT] Waiting {wait_time} seconds before next purchase...")
        time.sleep(wait_time)

if __name__ == "__main__":
    run_bot()
