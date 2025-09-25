import os
import json
import time
import pika
import httpx
from dotenv import load_dotenv
from tools.geo import distancia_km

load_dotenv()

AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_PORT = int(os.getenv("AMQP_PORT", "5672"))
AMQP_USER = os.getenv("AMQP_USER", "guest")
AMQP_PASS = os.getenv("AMQP_PASS", "guest")
HTTP_BASE = os.getenv("HTTP_BASE", "http://api:8000")
UMBRAL_KM = float(os.getenv("UMBRAL_KM", "500"))

CITY_NAME = os.getenv("CITY_NAME", "Valparaíso")
CITY_LAT = float(os.getenv("CITY_LAT", "-33.0360"))
CITY_LON = float(os.getenv("CITY_LON", "-71.6296"))

EXCHANGE_NAME = "quakes"

def on_msg(ch, method, properties, body):
    # body: bytes -> str -> dict
    try:
        ev = json.loads(body.decode("utf-8"))
    except Exception as e:
        print(f"[{CITY_NAME}] Invalid message body: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Esperamos claves: id, lat, lon
    qid = ev.get("id")
    lat = ev.get("lat")
    lon = ev.get("lon")

    if qid is None or lat is None or lon is None:
        print(f"[{CITY_NAME}] Missing keys in event (need id, lat, lon): {ev}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        d = distancia_km(CITY_LAT, CITY_LON, float(lat), float(lon))
    except Exception as e:
        print(f"[{CITY_NAME}] Distance error: {e} | ev={ev}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if d <= UMBRAL_KM:
        try:
            r = httpx.get(f"{HTTP_BASE}/quakes/{qid}", timeout=5.0)
            if r.status_code == 200:
                detail = r.json()
                print(f"[{CITY_NAME}] Interesa (dist={d:.1f}km): {detail.get('id')}")
            else:
                print(f"[{CITY_NAME}] Detalle no disponible (HTTP {r.status_code}): {qid}")
        except Exception as e:
            print(f"[{CITY_NAME}] Error HTTP: {e}")
    else:
        print(f"[{CITY_NAME}] Ignorado (dist={d:.1f}km) > {UMBRAL_KM}km")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def connect_with_retry(max_attempts=30):
    creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
    for attempt in range(1, max_attempts + 1):
        try:
            return pika.BlockingConnection(params)
        except Exception as e:
            wait = min(2 ** attempt, 30)
            print(f"[{CITY_NAME}] AMQP connect {attempt}/{max_attempts} failed: {e}. Retrying in {wait}s")
            time.sleep(wait)
    return None

if __name__ == "__main__":
    print(f"[{CITY_NAME}] Booting subscriber… UMBRAL={UMBRAL_KM} km (HTTP={HTTP_BASE})", flush=True)

    conn = connect_with_retry()
    if conn is None:
        raise SystemExit(f"[{CITY_NAME}] Could not connect to RabbitMQ")

    ch = conn.channel()
    # fanout para broadcast de sismos
    ch.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout", durable=True)

    queue_name = f"quakes.{CITY_NAME.replace(' ','_')}"
    ch.queue_declare(queue=queue_name, durable=True)
    ch.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue_name, on_message_callback=on_msg)

    print(f"[{CITY_NAME}] Ready. Waiting for messages…", flush=True)
    ch.start_consuming()
