import pika
import json
import time
from models import get_db_connection

def process_order(ch, method, properties, body):
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"[!] Received invalid JSON: {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if not isinstance(data, dict):
        print(f"[!] Received unexpected data type: {type(data)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    username = data.get("username")
    product_ids = data.get("product_ids")

    if not username or not product_ids:
        print(f"[!] Missing fields in message: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    conn = get_db_connection()
    cur = conn.cursor()
    for pid in product_ids:
        cur.execute(
            "INSERT INTO orders (username, product_id) VALUES (%s, %s)",
            (username, pid)
        )
    conn.commit()
    cur.close()
    conn.close()

    print(f"[✓] Order processed for {username}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    rabbitmq_urls = [
        "amqp://guest:guest@rabbitmq1:5672/%2F",
        "amqp://guest:guest@rabbitmq2:5672/%2F",
        "amqp://guest:guest@rabbitmq3:5672/%2F"
    ]

    connection = None
    for attempt in range(1, 31):
        for url in rabbitmq_urls:
            try:
                print(f"Trying RabbitMQ node: {url}")
                parameters = pika.URLParameters(url)
                connection = pika.BlockingConnection(parameters)
                print(f"[✓] Connected to RabbitMQ at {url}")
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"[!] Could not connect to {url}. Trying next node...")
                time.sleep(2)
        if connection:
            break
        print(f"[!] RabbitMQ cluster not ready yet (attempt {attempt}/30). Retrying in 5s...")
        time.sleep(5)
    else:
        print("[✗] Could not connect to any RabbitMQ node after multiple attempts. Exiting.")
        return

    channel = connection.channel()
    channel.queue_declare(queue='order_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='order_queue', on_message_callback=process_order)

    print("[*] Waiting for orders. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Worker stopped manually.")
        connection.close()

if __name__ == "__main__":
    main()
