import pika
import json
from models import get_db_connection

def process_order(ch, method, properties, body):
    data = json.loads(body)
    username = data["username"]
    product_ids = data["product_ids"]

    conn = get_db_connection()
    cur = conn.cursor()
    for pid in product_ids:
        cur.execute("INSERT INTO orders (username, product_id) VALUES (%s, %s)", (username, pid))
    conn.commit()
    cur.close()
    conn.close()

    print(f"[✓] Order processed for {username}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='order_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='order_queue', on_message_callback=process_order)
    print("[*] Waiting for orders. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
