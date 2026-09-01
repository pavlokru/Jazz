# api.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from core import CatalogEngine

app = FastAPI(
    title="JazzCatalog API (RAG)",
    description="Motor RAG optimizado para Edge/ARM64",
    version="1.0.0"
)

# El motor mantiene su carga lazy interna.
engine = CatalogEngine()

# --- ESQUEMAS DE VALIDACIÓN (PYDANTIC) ---

class ArtistaIn(BaseModel):
    nombre: str
    origen: str
    corriente: List[str]
    instrumento: List[str]
    tipo_agrupacion: str
    agrupaciones_propias: List[str]
    colaboraciones_clave: List[str]
    albumes_fundamentales: List[str]
    anio_inicio: Optional[int] = None
    anio_fin: Optional[int] = None

class NotaIn(BaseModel):
    nota: str

# --- ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    """Genera embeddings faltantes al levantar el servidor."""
    engine.generar_embeddings_faltantes()

@app.get("/catalogo", response_model=List[dict])
def obtener_todos():
    return engine.obtener_todos()

@app.get("/buscar", response_model=List[dict])
def buscar(q: str = Query(..., min_length=1), umbral: float = 0.3):
    return engine.buscar(q, umbral)

@app.get("/catalogo/{item_id}", response_model=dict)
def obtener_por_id(item_id: int):
    item = engine.obtener_por_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    return item

@app.post("/catalogo", response_model=dict)
def agregar_item(artista: ArtistaIn):
    # Compatibilidad con Pydantic v1 y v2
    data = artista.model_dump() if hasattr(artista, "model_dump") else artista.dict()
    return engine.agregar_item(**data)

@app.post("/catalogo/{item_id}/nota")
def agregar_nota(item_id: int, payload: NotaIn):
    exito = engine.agregar_nota(item_id, payload.nota)
    if not exito:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    return {"status": "ok", "message": "Nota anexada correctamente"}

