import os
import json
import time
import sys
import pika
import httpx
from dotenv import load_dotenv
from tools.geo import distancia_km

load_dotenv()

AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_PORT = int(os.getenv("AMQP_PORT", "5672"))
AMQP_USER = os.getenv("AMQP_USER", "guest")
AMQP_PASS = os.getenv("AMQP_PASS", "guest")
AMQP_QUEUE = os.getenv("AMQP_QUEUE", "quakes")
HTTP_BASE = os.getenv("HTTP_BASE", "http://api:8000")
UMBRAL_KM = float(os.getenv("UMBRAL_KM", "500"))

CITY_NAME = os.getenv("CITY_NAME", "Valparaíso")
CITY_LAT = float(os.getenv("CITY_LAT", "-33.0360"))
CITY_LON = float(os.getenv("CITY_LON", "-71.6296"))


def on_msg(ch, method, props, body):
	try:
		ev = json.loads(body)
	except Exception as e:
		print(f"[{CITY_NAME}] Invalid message body: {e}")
		ch.basic_ack(delivery_tag=method.delivery_tag)
		return

	d = distancia_km(CITY_LAT, CITY_LON, float(ev.get("lat", 0)), float(ev.get("lon", 0)))
	if d <= UMBRAL_KM:
		try:
			r = httpx.get(f"{HTTP_BASE}/quakes/{ev.get('id')}", timeout=5.0)
			if r.status_code == 200:
				print(f"[{CITY_NAME}] Interesa (dist={d:.1f}km): {r.json().get('id')}")
			else:
				print(f"[{CITY_NAME}] Detalle no disponible: {ev.get('id')}")
		except Exception as e:
			print(f"[{CITY_NAME}] Error HTTP: {e}")
	else:
		print(f"[{CITY_NAME}] Ignorado (dist={d:.1f}km)")

	ch.basic_ack(delivery_tag=method.delivery_tag)


def connect_with_retry(max_attempts=10):
	creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
	params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
	attempt = 0
	while attempt < max_attempts:
		try:
			conn = pika.BlockingConnection(params)
			return conn
		except Exception as e:
			attempt += 1
			wait = min(2 ** attempt, 30)
			print(f"[{CITY_NAME}] AMQP connect attempt {attempt}/{max_attempts} failed: {e}. Retrying in {wait}s")
			time.sleep(wait)
	return None


if __name__ == "__main__":
	print(f"[{CITY_NAME}] Starting subscriber. Connecting to AMQP={AMQP_HOST}:{AMQP_PORT}, HTTP={HTTP_BASE}, UMBRAL={UMBRAL_KM}km")
	conn = connect_with_retry(max_attempts=int(os.getenv("AMQP_CONNECT_RETRIES", "12")))
	if conn is None:
		print(f"[{CITY_NAME}] Failed to connect to RabbitMQ after retries. Exiting.")
		sys.exit(1)

	ch = conn.channel()
	ch.queue_declare(queue=AMQP_QUEUE, durable=True)
	ch.basic_qos(prefetch_count=1)
	ch.basic_consume(queue=AMQP_QUEUE, on_message_callback=on_msg)

	print(f"[{CITY_NAME}] Esperando sismos… UMBRAL={UMBRAL_KM} km (HTTP={HTTP_BASE})")
	try:
		ch.start_consuming()
	except KeyboardInterrupt:
		print(f"[{CITY_NAME}] Interrupted, closing connection")
		try:
			conn.close()
		except Exception:
			pass
