from fastapi import FastAPI, HTTPException

app = FastAPI(title="Datos Sismos (in-memory)")

DB = {
    "us-2025abcd": {
        "id":"us-2025abcd","origen":"USGS","lat":-33.45,"lon":-70.66,
        "mag":5.9,"prof_km":80,"zona":"RM","reporte":"Sismo sentido..."
    }
}

@app.get("/quakes/{qid}")
def get_quake(qid: str):
    q = DB.get(qid)
    if not q:
        raise HTTPException(status_code=404, detail="No existe sismo")
    return q

@app.get("/healthz")
def healthz():
    return {"status":"ok"}
