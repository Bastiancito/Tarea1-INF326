from fastapi import FastAPI, HTTPException
from typing import Dict, Optional, Any, List
from pydantic import BaseModel
import os, json, time
import pika

app = FastAPI(title="Datos Sismos (in-memory)")

# -----------------------------
# Base de datos en memoria
# -----------------------------
DB: Dict[str, dict] = {
    "us-2025abcd": {
        "id": "us-2025abcd", "origen": "USGS", "lat": -33.45, "lon": -70.66,
        "mag": 5.9, "prof_km": 80, "zona": "RM", "reporte": "Sismo sentido..."
    },
    "cl-2025efgh": {
        "id": "cl-2025efgh", "origen": "CSN", "lat": -36.82, "lon": -73.05,
        "mag": 6.2, "prof_km": 25, "zona": "Biobío", "reporte": "Movimiento fuerte en Concepción."
    },
    "cl-2025ijkl": {
        "id": "cl-2025ijkl", "origen": "CSN", "lat": -27.37, "lon": -70.33,
        "mag": 5.4, "prof_km": 50, "zona": "Atacama", "reporte": "Sismo moderado en Copiapó."
    },
    "cl-2025mnop": {
        "id": "cl-2025mnop", "origen": "CSN", "lat": -41.47, "lon": -72.94,
        "mag": 4.8, "prof_km": 15, "zona": "Los Lagos", "reporte": "Sismo leve en Puerto Montt."
    },
    "cl-2025qrst": {
        "id": "cl-2025qrst", "origen": "CSN", "lat": -20.21, "lon": -70.15,
        "mag": 6.0, "prof_km": 90, "zona": "Tarapacá", "reporte": "Sismo perceptible en Iquique."
    },
    "cl-2025uvwx": {
        "id": "cl-2025uvwx", "origen": "CSN", "lat": -23.65, "lon": -70.40,
        "mag": 5.7, "prof_km": 40, "zona": "Antofagasta", "reporte": "Movimiento moderado en la costa."
    },
    "cl-2025yz01": {
        "id": "cl-2025yz01", "origen": "CSN", "lat": -35.42, "lon": -71.66,
        "mag": 4.9, "prof_km": 10, "zona": "Maule", "reporte": "Sismo superficial en Talca."
    },
    "cl-2025yz02": {
        "id": "cl-2025yz02", "origen": "CSN", "lat": -39.83, "lon": -73.25,
        "mag": 5.3, "prof_km": 30, "zona": "Los Ríos", "reporte": "Sismo moderado en Valdivia."
    },
    "cl-2025yz03": {
        "id": "cl-2025yz03", "origen": "CSN", "lat": -18.47, "lon": -70.30,
        "mag": 4.6, "prof_km": 12, "zona": "Arica y Parinacota", "reporte": "Movimiento leve en Arica."
    },
    "cl-2025yz04": {
        "id": "cl-2025yz04", "origen": "CSN", "lat": -29.90, "lon": -71.25,
        "mag": 6.5, "prof_km": 100, "zona": "Coquimbo", "reporte": "Sismo fuerte en La Serena."
    },
    "cl-2025yz05": {
        "id": "cl-2025yz05", "origen": "CSN", "lat": -42.48, "lon": -73.76,
        "mag": 5.0, "prof_km": 20, "zona": "Chiloé", "reporte": "Sismo leve sentido en Castro."
    },
    "cl-2025yz06": {
        "id": "cl-2025yz06", "origen": "CSN", "lat": -53.16, "lon": -70.91,
        "mag": 4.3, "prof_km": 18, "zona": "Magallanes", "reporte": "Sismo débil en Punta Arenas."
    },
    "cl-2025yz07": {
        "id": "cl-2025yz07", "origen": "CSN", "lat": -33.65, "lon": -71.61,
        "mag": 5.6, "prof_km": 70, "zona": "Valparaíso", "reporte": "Sismo moderado en la costa."
    },
    "cl-2025yz08": {
        "id": "cl-2025yz08", "origen": "CSN", "lat": -32.83, "lon": -70.60,
        "mag": 4.7, "prof_km": 15, "zona": "Valparaíso", "reporte": "Sismo leve en Los Andes."
    },
    "cl-2025yz09": {
        "id": "cl-2025yz09", "origen": "CSN", "lat": -34.58, "lon": -70.98,
        "mag": 5.1, "prof_km": 22, "zona": "O’Higgins", "reporte": "Sismo percibido en Rancagua."
    }
}

# -----------------------------
# Endpoints de lectura
# -----------------------------
@app.get("/quakes")
def list_quakes():
    return list(DB.values())

@app.get("/quakes/{qid}")
def get_quake(qid: str):
    q = DB.get(qid)
    if not q:
        raise HTTPException(status_code=404, detail="No existe sismo")
    return q

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# -----------------------------
# Publicación a RabbitMQ (fanout)
# -----------------------------
AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_PORT = int(os.getenv("AMQP_PORT", "5672"))
AMQP_USER = os.getenv("AMQP_USER", "guest")
AMQP_PASS = os.getenv("AMQP_PASS", "guest")
EXCHANGE_NAME = "quakes"  # fanout (broadcast)

def _amqp_channel():
    """Crea conexión y canal; declara el exchange fanout."""
    creds = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(host=AMQP_HOST, port=AMQP_PORT, credentials=creds)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout", durable=True)
    return conn, ch

def _publish_many(msgs: List[Dict[str, Any]]) -> None:
    """Publica una lista de mensajes JSON al exchange fanout."""
    conn, ch = _amqp_channel()
    try:
        for m in msgs:
            ch.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key="",
                body=json.dumps(m, ensure_ascii=False).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2  # persistente
                ),
            )
    finally:
        conn.close()

# -----------------------------
# Endpoint para publicar sismos
# -----------------------------
class PublishRequest(BaseModel):
    message: Optional[Dict[str, Any]] = None
    # Si viene "message", se publica solo ese JSON.
    # Si no viene, se publican todos los del DB (15).

@app.post("/quakes/publish")
def publish_quakes(req: PublishRequest):
    """
    Publica sismos en RabbitMQ:
      - Si se envía {"message": {...}} -> publica sólo ese mensaje.
      - Si no se envía "message" -> publica todos los del DB con time=now.
    Devuelve el resumen y los mensajes para verificarlos en Postman.
    """
    now = int(time.time())

    if req.message is not None:
        msg = dict(req.message)
        msg.setdefault("time", now)
        _publish_many([msg])
        return {
            "mode": "single",
            "published": 1,
            "ids": [msg.get("id")],
            "messages": [msg],
        }

    # Publicación masiva: todos los sismos del DB
    messages = []
    for q in DB.values():
        m = dict(q)
        m["time"] = now
        messages.append(m)

    _publish_many(messages)
    return {
        "mode": "db_batch",
        "published": len(messages),
        "ids": [m.get("id") for m in messages],
        "messages": messages,
    }
