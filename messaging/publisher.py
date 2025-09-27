import os
import json
import time
import argparse
import pika
from dotenv import load_dotenv
from messaging.config import AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASS, AMQP_QUEUE, EXCHANGE_NAME

load_dotenv()


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


def publish_many(messages: list, exchange_name: str = None):
    creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    if exchange_name is None:
        exchange_name = EXCHANGE_NAME

    ch.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)

    for body in messages:
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
            messages = [body]   
        except Exception as e:
            print(f"Invalid JSON: {e}")
            return
    else:
        now = int(time.time())
        messages = list_quakes()
        for m in messages:
            m["time"] = now

    for quake in messages:
        publish_message(quake)
        print(f"Published message to {AMQP_QUEUE}: {quake.get('id','<no-id>')}")



HARDCODED_DB = {}


def load_sample_db():
    sample = {
        "us-2025abcd": {"id": "us-2025abcd", "lat": -33.45, "lon": -70.66, "origen": "USGS", "mag": 5.9, "prof_km": 80, "zona": "RM", "reporte": "Sismo sentido..."},
        "cl-2025efgh": {"id": "cl-2025efgh", "lat": -36.82, "lon": -73.05, "origen": "CSN", "mag": 6.2, "prof_km": 25, "zona": "Biobío", "reporte": "Movimiento fuerte en Concepción."},
        "cl-2025ijkl": {"id": "cl-2025ijkl", "lat": -27.37, "lon": -70.33, "origen": "CSN", "mag": 5.4, "prof_km": 50, "zona": "Atacama", "reporte": "Sismo moderado en Copiapó."},
        "cl-2025mnop": {"id": "cl-2025mnop", "lat": -41.47, "lon": -72.94, "origen": "CSN", "mag": 4.8, "prof_km": 15, "zona": "Los Lagos", "reporte": "Sismo leve en Puerto Montt."},
        "cl-2025qrst": {"id": "cl-2025qrst", "lat": -20.21, "lon": -70.15, "origen": "CSN", "mag": 6.0, "prof_km": 90, "zona": "Tarapacá", "reporte": "Sismo perceptible en Iquique."},
        "cl-2025uvwx": {"id": "cl-2025uvwx", "lat": -23.65, "lon": -70.4, "origen": "CSN", "mag": 5.7, "prof_km": 40, "zona": "Antofagasta", "reporte": "Movimiento moderado en la costa."},
        "cl-2025yz01": {"id": "cl-2025yz01", "lat": -35.42, "lon": -71.66, "origen": "CSN", "mag": 4.9, "prof_km": 10, "zona": "Maule", "reporte": "Sismo superficial en Talca."},
        "cl-2025yz02": {"id": "cl-2025yz02", "lat": -39.83, "lon": -73.25, "origen": "CSN", "mag": 5.3, "prof_km": 30, "zona": "Los Ríos", "reporte": "Sismo moderado en Valdivia."},
        "cl-2025yz03": {"id": "cl-2025yz03", "lat": -18.47, "lon": -70.3, "origen": "CSN", "mag": 4.6, "prof_km": 12, "zona": "Arica y Parinacota", "reporte": "Movimiento leve en Arica."},
        "cl-2025yz04": {"id": "cl-2025yz04", "lat": -29.9, "lon": -71.25, "origen": "CSN", "mag": 6.5, "prof_km": 100, "zona": "Coquimbo", "reporte": "Sismo fuerte en La Serena."},
        "cl-2025yz05": {"id": "cl-2025yz05", "lat": -42.48, "lon": -73.76, "origen": "CSN", "mag": 5.0, "prof_km": 20, "zona": "Chiloé", "reporte": "Sismo leve sentido en Castro."},
        "cl-2025yz06": {"id": "cl-2025yz06", "lat": -53.16, "lon": -70.91, "origen": "CSN", "mag": 4.3, "prof_km": 18, "zona": "Magallanes", "reporte": "Sismo débil en Punta Arenas."},
        "cl-2025yz07": {"id": "cl-2025yz07", "lat": -33.65, "lon": -71.61, "origen": "CSN", "mag": 5.6, "prof_km": 70, "zona": "Valparaíso", "reporte": "Sismo moderado en la costa."},
        "cl-2025yz08": {"id": "cl-2025yz08", "lat": -32.83, "lon": -70.6, "origen": "CSN", "mag": 4.7, "prof_km": 15, "zona": "Valparaíso", "reporte": "Sismo leve en Los Andes."},
        "cl-2025yz09": {"id": "cl-2025yz09", "lat": -34.58, "lon": -70.98, "origen": "CSN", "mag": 5.1, "prof_km": 22, "zona": "O’Higgins", "reporte": "Sismo percibido en Rancagua."},
    }
    HARDCODED_DB.clear()
    HARDCODED_DB.update(sample)


def list_quakes():
    return [dict(v) for v in HARDCODED_DB.values()]


def get_quake(qid: str):
    q = HARDCODED_DB.get(qid)
    return dict(q) if q is not None else None


def get_random_quake():
    import random as _r
    values = list(HARDCODED_DB.values())
    if not values:
        return None
    q = _r.choice(values)
    return dict(q)


def save_quake(msg: dict):
    if not isinstance(msg, dict):
        return
    qid = msg.get("id")
    if qid:
        HARDCODED_DB[qid] = dict(msg)


if __name__ == "__main__":
    main()
