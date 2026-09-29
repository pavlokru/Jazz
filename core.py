import sqlite3
import json
import os
import gc
import numpy as np
from typing import Dict, List, Optional

# --- PROTECCIÓN ESTRICTA CONTRA THROTTLING (Streamlit Cloud) ---
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class CatalogEngine:
    """Motor RAG y persistencia SQLite optimizado para bajo footprint de RAM y CPU."""

    def __init__(
        self,
        db_path: str = "data/catalogo.db",
        datos_iniciales: Optional[List[Dict]] = None,
    ):
        self.db_path = db_path
        self.modelo_embeddings = None  # Carga Lazy (Perezosa)
        self._preparar_entorno()
        self._inicializar_db()
        self._actualizar_esquema_v2()
        if datos_iniciales:
            self._sincronizar_datos_iniciales(datos_iniciales)

    def _preparar_entorno(self):
        directorio = os.path.dirname(self.db_path)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artistas (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    origen TEXT,
                    corriente TEXT,
                    instrumento TEXT,
                    tipo_agrupacion TEXT,
                    agrupaciones_propias TEXT,
                    colaboraciones_clave TEXT,
                    albumes_fundamentales TEXT,
                    anio_inicio INTEGER,
                    anio_fin INTEGER,
                    nota TEXT
                )
            """)

    def _actualizar_esquema_v2(self):
        with self._conectar() as conn:
            try:
                conn.execute("ALTER TABLE artistas ADD COLUMN embedding BLOB")
            except sqlite3.OperationalError:
                pass 

    def _sincronizar_datos_iniciales(self, datos: List[Dict]):
        with self._conectar() as conn:
            for item in datos:
                cursor = conn.execute("SELECT id FROM artistas WHERE id = ?", (item["id"],))
                if not cursor.fetchone():
                    self._insertar_registro(conn, item)

    def _insertar_registro(self, conn, item: Dict):
        conn.execute("""
            INSERT INTO artistas (
                id, nombre, origen, corriente, instrumento, tipo_agrupacion,
                agrupaciones_propias, colaboraciones_clave, albumes_fundamentales,
                anio_inicio, anio_fin, nota
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"),
            item.get("nombre"),
            item.get("origen"),
            json.dumps(item.get("corriente", [])),
            json.dumps(item.get("instrumento", [])),
            item.get("tipo_agrupacion"),
            json.dumps(item.get("agrupaciones_propias", [])),
            json.dumps(item.get("colaboraciones_clave", [])),
            json.dumps(item.get("albumes_fundamentales", [])),
            item.get("anio_inicio"),
            item.get("anio_fin"),
            item.get("nota")
        ))

    def _fila_a_dict(self, fila) -> Dict:
        d = dict(fila)
        campos_lista = ["corriente", "instrumento", "agrupaciones_propias", "colaboraciones_clave", "albumes_fundamentales"]
        for campo in campos_lista:
            d[campo] = json.loads(d[campo]) if d.get(campo) else []
        
        # Eliminar el BLOB para no sobrecargar la RAM en la UI
        d.pop("embedding", None)
        return d

    def _cargar_modelo(self):
        """Instancia el modelo solo cuando es estrictamente necesario, limitando CPU."""
        if self.modelo_embeddings is None:
            import torch
            
            # Protección contra reejecuciones
            try:
                torch.set_num_threads(1)
                torch.set_num_interop_threads(1)
            except RuntimeError:
                pass
            
            from sentence_transformers import SentenceTransformer
            self.modelo_embeddings = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
        return self.modelo_embeddings

    def _texto_a_vector(self, texto: str) -> bytes:
        modelo = self._cargar_modelo()
        vector = modelo.encode(texto, convert_to_numpy=True)
        return vector.astype(np.float32).tobytes()

    def generar_embeddings_faltantes(self):
        """Genera vectores ÚNICAMENTE para registros nuevos o actualizados."""
        with self._conectar() as conn:
            filas = conn.execute("SELECT * FROM artistas WHERE embedding IS NULL").fetchall()
            if not filas:
                return 0
            
            for fila in filas:
                d = self._fila_a_dict(fila)
                # NOTA: Se incluye la biografía ('nota') en el texto base para la búsqueda semántica
                texto_nota = d.get("nota", "") or ""
                doc = (
                    f"{d['nombre']}. "
                    f"Origen: {d.get('origen', '')}. "
                    f"Estilos: {' '.join(d.get('corriente', []))}. "
                    f"Instrumentos: {' '.join(d.get('instrumento', []))}. "
                    f"Biografía y Apuntes: {texto_nota}"
                )
                vector_bytes = self._texto_a_vector(doc)
                conn.execute("UPDATE artistas SET embedding = ? WHERE id = ?", (vector_bytes, d["id"]))
            
            # Recolector de basura forzado para liberar tensores de la memoria
            gc.collect()
            return len(filas)

    def buscar(self, criterio: str, umbral: float = 0.3) -> List[Dict]:
        criterio_norm = criterio.strip()
        if not criterio_norm:
            return self.obtener_todos()

        vector_query = self._cargar_modelo().encode(criterio_norm, convert_to_numpy=True)
        
        resultados = []
        with self._conectar() as conn:
            filas = conn.execute("SELECT * FROM artistas WHERE embedding IS NOT NULL").fetchall()
            
            for fila in filas:
                vector_db = np.frombuffer(fila["embedding"], dtype=np.float32)
                similitud = np.dot(vector_query, vector_db) / (np.linalg.norm(vector_query) * np.linalg.norm(vector_db))
                
                if similitud >= umbral:
                    d = self._fila_a_dict(fila)
                    d["_score"] = float(similitud)
                    resultados.append(d)

        resultados.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return resultados

    def obtener_todos(self) -> List[Dict]:
        with self._conectar() as conn:
            filas = conn.execute("SELECT * FROM artistas ORDER BY nombre ASC").fetchall()
            return [self._fila_a_dict(f) for f in filas]

    def agregar_nota(self, item_id: int, nueva_nota: str) -> bool:
        with self._conectar() as conn:
            fila = conn.execute("SELECT nota FROM artistas WHERE id = ?", (item_id,)).fetchone()
            if not fila:
                return False
            
            nota_actual = fila["nota"]
            nota_final = f"{nota_actual}\n\n• {nueva_nota}" if nota_actual else f"• {nueva_nota}"
            
            # CRÍTICO: Poner embedding = NULL obliga a recalcular el vector de este artista
            # en la próxima llamada a generar_embeddings_faltantes().
            conn.execute("UPDATE artistas SET nota = ?, embedding = NULL WHERE id = ?", (nota_final, item_id))
            return True

    def agregar_item(self, nombre: str, origen: str, corriente: List[str], instrumento: List[str], tipo_agrupacion: str, agrupaciones_propias: List[str], colaboraciones_clave: List[str], albumes_fundamentales: List[str], anio_inicio: Optional[int], anio_fin: Optional[int]) -> Dict:
        with self._conectar() as conn:
            cursor = conn.execute("SELECT MAX(id) FROM artistas")
            max_id = cursor.fetchone()[0]
            nuevo_id = (max_id or 0) + 1

            nuevo_item = {
                "id": nuevo_id,
                "nombre": nombre,
                "origen": origen,
                "corriente": corriente,
                "instrumento": instrumento,
                "tipo_agrupacion": tipo_agrupacion,
                "agrupaciones_propias": agrupaciones_propias,
                "colaboraciones_clave": colaboraciones_clave,
                "albumes_fundamentales": albumes_fundamentales,
                "anio_inicio": anio_inicio,
                "anio_fin": anio_fin,
                "nota": None
            }
            self._insertar_registro(conn, nuevo_item)
            
        self.generar_embeddings_faltantes()
        return nuevo_item

