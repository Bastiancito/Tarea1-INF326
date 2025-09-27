from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import time
from datetime import datetime
from messaging.publisher import publish_many, get_random_quake, save_quake, list_quakes
import messaging.publisher as publisher
from messaging.utils import distancia_km
from messaging.config import SUBSCRIBERS, UMBRAL_KM
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

REGIONS_STATS: Dict[str, Dict[str, Any]] = {}


def normalizar_region(name: str) -> str:
    if not name:
        return name
    import unicodedata
    s = name.replace("_", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.split())
    return s.title()


class RegionReport(BaseModel):
    region: str
    status: str
    quake: Optional[dict] = None


@app.post("/regions/report")
def region_report(r: RegionReport):
    region_raw = r.region or ""
    region = normalizar_region(region_raw)
    status = (r.status or "").lower()
    if status not in ("ignored", "interest"):
        raise HTTPException(status_code=400, detail="status debe ser 'ignored' o 'interest'")
    stats = REGIONS_STATS.setdefault(region, {"ignored": 0, "interest": 0, "published": 0, "ignored_list": [], "interest_list": []})
    stats["published"] = stats.get("published", 0) + 1
    stats[status] = stats.get(status, 0) + 1
    if r.quake is not None:
        list_key = "interest_list" if status == "interest" else "ignored_list"
        try:
            stats[list_key].append(dict(r.quake))
        except Exception:
            stats[list_key].append(r.quake)
    return {"region": region, "status": status, "current": stats}


@app.post("/quakes/publish")
def publish_quakes():
    msg = get_random_quake()
    if not msg:
        try:
            if hasattr(publisher, "load_sample_db"):
                publisher.load_sample_db()
        except Exception:
            pass
        msg = get_random_quake()
    if not msg:
        raise HTTPException(status_code=404, detail="No hay sismos en la DB para publicar")
    now = int(time.time())
    msg = dict(msg)
    msg["hora_utc"] = datetime.utcfromtimestamp(now).isoformat() + "Z"
    if msg.get("id"):
        save_quake(msg)
    publish_many([msg])
    interesados = []
    ignorados = []
    lat = msg.get("lat")
    lon = msg.get("lon")
    for region, info in SUBSCRIBERS.items():
        try:
            d = distancia_km(info["lat"], info["lon"], float(lat), float(lon))
        except Exception:
            ignorados.append(region)
            continue
        if d <= UMBRAL_KM:
            interesados.append({"region": region, "distancia_km": round(d, 2)})
        else:
            ignorados.append({"region": region, "distancia_km": round(d, 2)})
    resp_msg = dict(msg)
    resp_msg.pop("time", None)
    return {"publicado": resp_msg, "interesados": interesados, "ignorados": ignorados}


@app.get("/regions/totals")
def regions_totals():
    result: Dict[str, Dict[str, Any]] = {}
    for k in REGIONS_STATS.keys():
        r = normalizar_region(k)
        result.setdefault(r, {"cantidad_ignorados": 0, "cantidad_interes": 0, "lista_ignorados": [], "lista_interes": []})
    for k in SUBSCRIBERS.keys():
        r = normalizar_region(k)
        result.setdefault(r, {"cantidad_ignorados": 0, "cantidad_interes": 0, "lista_ignorados": [], "lista_interes": []})
    for region_key, mem in REGIONS_STATS.items():
        r = normalizar_region(region_key)
        entry = result.setdefault(r, {"cantidad_ignorados": 0, "cantidad_interes": 0, "lista_ignorados": [], "lista_interes": []})
        entry["cantidad_ignorados"] = mem.get("ignored", 0)
        entry["cantidad_interes"] = mem.get("interest", 0)
        entry["lista_ignorados"] = mem.get("ignored_list") or mem.get("lista_ignorados") or []
        entry["lista_interes"] = mem.get("interest_list") or mem.get("lista_interes") or []
    return result


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
