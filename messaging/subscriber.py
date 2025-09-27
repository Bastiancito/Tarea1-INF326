import os
import json
import time
import pika
import httpx
from dotenv import load_dotenv
from messaging.utils import distancia_km
from messaging.config import AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASS, EXCHANGE_NAME, UMBRAL_KM

load_dotenv()

HTTP_BASE = os.getenv("HTTP_BASE", "http://api:8000")
CITY_NAME = os.getenv("CITY_NAME", "Valparaíso")
CITY_LAT = float(os.getenv("CITY_LAT", "-33.0360"))
CITY_LON = float(os.getenv("CITY_LON", "-71.6296"))

def on_msg(ch, method, _properties, body):
    try:
        ev = json.loads(body.decode("utf-8"))
    except Exception as e:
        print(f"[{CITY_NAME}] ❌ Mensaje inválido: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    qid = ev.get("id")
    lat = ev.get("lat")
    lon = ev.get("lon")

    if qid is None or lat is None or lon is None:
        print(f"[{CITY_NAME}] ⚠️ Faltan claves en el evento (se requieren id, lat, lon): {ev}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        d = distancia_km(CITY_LAT, CITY_LON, float(lat), float(lon))
    except Exception as e:
        print(f"[{CITY_NAME}] ❌ Error calculando distancia: {e} | evento={ev}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return


    if d <= UMBRAL_KM:
        detail = None
        try:
            r = httpx.get(f"{HTTP_BASE}/quakes/{qid}", timeout=5.0)
            if r.status_code == 200:
                detail = r.json()
            else:
                detail = ev
        except Exception:
            detail = ev
        id_ = detail.get("id") or "<sin-id>"
        mag = detail.get("mag") or "<no-mag>"
        hora = detail.get("hora_utc") or detail.get("time") or "<hora desconocida>"
        lugar = detail.get("place") or detail.get("place_name") or detail.get("title") or detail.get("zona") or detail.get("reporte") or "<lugar desconocido>"
        profundidad = detail.get("depth") or detail.get("prof_km") or "<profundidad desconocida>"
        lat_d = detail.get("lat") or "<lat?>"
        lon_d = detail.get("lon") or "<lon?>"
        print(
            f"[{CITY_NAME}] ✅ Sismo relevante a {d:.1f} km: {id_} — magnitud {mag}, hora UTC {hora}, lugar: {lugar}, profundidad: {profundidad} km, coordenadas: {lat_d},{lon_d}.",
            flush=True,
        )
        try:
            httpx.post(f"{HTTP_BASE}/regions/report", json={
                "region": CITY_NAME,
                "status": "interest",
                "quake": detail,
            }, timeout=3.0)
        except Exception:
            pass
    else:
        print(f"[{CITY_NAME}] Sismo ignorado (distancia={d:.1f} km > {UMBRAL_KM} km) de magnitud {ev.get('mag','<no-mag>')}")
        try:
            httpx.post(f"{HTTP_BASE}/regions/report", json={
                "region": CITY_NAME,
                "status": "ignored",
                "quake": ev,
            }, timeout=3.0)
        except Exception:
            pass

    ch.basic_ack(delivery_tag=method.delivery_tag)


def connect_with_retry(max_attempts=30):
    creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
    for attempt in range(1, max_attempts + 1):
        try:
            return pika.BlockingConnection(params)
        except Exception as e:
            wait = min(2 ** attempt, 30)
            print(f"[{CITY_NAME}] 🔄 Conexión AMQP fallida {attempt}/{max_attempts}: {e}. Reintentando en {wait}s")
            time.sleep(wait)
    return None


if __name__ == "__main__":
    print(f"[{CITY_NAME}] 🚀 Iniciando suscriptor… UMBRAL={UMBRAL_KM} km (HTTP={HTTP_BASE})", flush=True)

    conn = connect_with_retry()
    if conn is None:
        raise SystemExit(f"[{CITY_NAME}] ❌ No se pudo conectar a RabbitMQ")

    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout", durable=True)

    queue_name = f"quakes.{CITY_NAME.replace(' ','_')}"
    ch.queue_declare(queue=queue_name, durable=True)
    ch.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue_name, on_message_callback=on_msg)

    print(f"[{CITY_NAME}] ✅ Listo. Esperando mensajes…", flush=True)
    ch.start_consuming()
