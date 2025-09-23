import os
import json
import time
import uuid
import argparse
import pika
from dotenv import load_dotenv

load_dotenv()

AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_PORT = int(os.getenv("AMQP_PORT", "5672"))
AMQP_USER = os.getenv("AMQP_USER", "guest")
AMQP_PASS = os.getenv("AMQP_PASS", "guest")
AMQP_QUEUE = os.getenv("AMQP_QUEUE", "quakes")


def publish_message(body: dict):
    creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    exchange_name = "quakes"
    ch.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)

    ch.basic_publish(
        exchange=exchange_name,
        routing_key='',
        body=json.dumps(body),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Publish a test quake to the quakes queue")
    parser.add_argument("--message", "-m", help="JSON string message to publish", default=None)
    args = parser.parse_args()

    if args.message:
        try:
            body = json.loads(args.message)
        except Exception as e:
            print(f"Invalid JSON: {e}")
            return
    else:
        now = int(time.time())

        body = {
            "id": "us-2025abcd",
            "lat": -33.45,
            "lon": -70.66,
            "origen": "USGS",
            "mag": 5.9,
            "time": now,
        }

    publish_message(body)
    print(f"Published message to {AMQP_QUEUE}: {body['id']}")


if __name__ == "__main__":
    main()
