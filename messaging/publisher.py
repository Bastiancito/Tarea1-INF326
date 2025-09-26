import os
import json
import time
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
        body=json.dumps(body, ensure_ascii=False),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json")
    )
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Publish quake(s) to the quakes queue")
    parser.add_argument("--message", "-m", help="JSON string message to publish", default=None)
    args = parser.parse_args()

    if args.message:
        try:
            body = json.loads(args.message)
            messages = [body]   # lista con un solo mensaje manual
        except Exception as e:
            print(f"Invalid JSON: {e}")
            return
    else:
        now = int(time.time())
        # Lista con 15 sismos de ejemplo
        messages = [
            {"id": "us-2025abcd", "lat": -33.45, "lon": -70.66, "origen": "USGS", "mag": 5.9, "prof_km": 80, "zona": "RM", "reporte": "Sismo sentido...", "time": now},
            {"id": "cl-2025efgh", "lat": -36.82, "lon": -73.05, "origen": "CSN", "mag": 6.2, "prof_km": 25, "zona": "Biobío", "reporte": "Movimiento fuerte en Concepción.", "time": now},
            {"id": "cl-2025ijkl", "lat": -27.37, "lon": -70.33, "origen": "CSN", "mag": 5.4, "prof_km": 50, "zona": "Atacama", "reporte": "Sismo moderado en Copiapó.", "time": now},
            {"id": "cl-2025mnop", "lat": -41.47, "lon": -72.94, "origen": "CSN", "mag": 4.8, "prof_km": 15, "zona": "Los Lagos", "reporte": "Sismo leve en Puerto Montt.", "time": now},
            {"id": "cl-2025qrst", "lat": -20.21, "lon": -70.15, "origen": "CSN", "mag": 6.0, "prof_km": 90, "zona": "Tarapacá", "reporte": "Sismo perceptible en Iquique.", "time": now},
            {"id": "cl-2025uvwx", "lat": -23.65, "lon": -70.40, "origen": "CSN", "mag": 5.7, "prof_km": 40, "zona": "Antofagasta", "reporte": "Movimiento moderado en la costa.", "time": now},
            {"id": "cl-2025yz01", "lat": -35.42, "lon": -71.66, "origen": "CSN", "mag": 4.9, "prof_km": 10, "zona": "Maule", "reporte": "Sismo superficial en Talca.", "time": now},
            {"id": "cl-2025yz02", "lat": -39.83, "lon": -73.25, "origen": "CSN", "mag": 5.3, "prof_km": 30, "zona": "Los Ríos", "reporte": "Sismo moderado en Valdivia.", "time": now},
            {"id": "cl-2025yz03", "lat": -18.47, "lon": -70.30, "origen": "CSN", "mag": 4.6, "prof_km": 12, "zona": "Arica y Parinacota", "reporte": "Movimiento leve en Arica.", "time": now},
            {"id": "cl-2025yz04", "lat": -29.90, "lon": -71.25, "origen": "CSN", "mag": 6.5, "prof_km": 100, "zona": "Coquimbo", "reporte": "Sismo fuerte en La Serena.", "time": now},
            {"id": "cl-2025yz05", "lat": -42.48, "lon": -73.76, "origen": "CSN", "mag": 5.0, "prof_km": 20, "zona": "Chiloé", "reporte": "Sismo leve sentido en Castro.", "time": now},
            {"id": "cl-2025yz06", "lat": -53.16, "lon": -70.91, "origen": "CSN", "mag": 4.3, "prof_km": 18, "zona": "Magallanes", "reporte": "Sismo débil en Punta Arenas.", "time": now},
            {"id": "cl-2025yz07", "lat": -33.65, "lon": -71.61, "origen": "CSN", "mag": 5.6, "prof_km": 70, "zona": "Valparaíso", "reporte": "Sismo moderado en la costa.", "time": now},
            {"id": "cl-2025yz08", "lat": -32.83, "lon": -70.60, "origen": "CSN", "mag": 4.7, "prof_km": 15, "zona": "Valparaíso", "reporte": "Sismo leve en Los Andes.", "time": now},
            {"id": "cl-2025yz09", "lat": -34.58, "lon": -70.98, "origen": "CSN", "mag": 5.1, "prof_km": 22, "zona": "O’Higgins", "reporte": "Sismo percibido en Rancagua.", "time": now},
        ]

    for quake in messages:
        publish_message(quake)
        print(f"Published message to {AMQP_QUEUE}: {quake['id']}")


if __name__ == "__main__":
    main()
