import sqlite3
import json
import os
from typing import Dict, List, Optional

class CatalogEngine:
    """Motor de persistencia SQLite optimizado para bajo footprint de RAM en ARM64."""

    def __init__(
        self,
        db_path: str = "data/catalogo.db",
        datos_iniciales: Optional[List[Dict]] = None,
    ):
        self.db_path = db_path
        self._preparar_entorno()
        self._inicializar_db()
        if datos_iniciales:
            self._sincronizar_datos_iniciales(datos_iniciales)

    def _preparar_entorno(self):
        """Asegura la existencia del directorio base para evitar errores de I/O."""
        directorio = os.path.dirname(self.db_path)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)

    def _conectar(self):
        """Conexión efímera. Permite al OS liberar recursos cuando no hay consultas."""
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

    def _sincronizar_datos_iniciales(self, datos: List[Dict]):
        """Carga en bloque sin sobreescribir IDs existentes (Evita O(N^2) en RAM)."""
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
        """Hidrata los campos JSON bajo demanda."""
        d = dict(fila)
        campos_lista = ["corriente", "instrumento", "agrupaciones_propias", "colaboraciones_clave", "albumes_fundamentales"]
        for campo in campos_lista:
            d[campo] = json.loads(d[campo]) if d.get(campo) else []
        return d

    def obtener_todos(self) -> List[Dict]:
        with self._conectar() as conn:
            filas = conn.execute("SELECT * FROM artistas ORDER BY id ASC").fetchall()
            return [self._fila_a_dict(f) for f in filas]

    def buscar(self, criterio: str) -> List[Dict]:
        criterio_norm = criterio.strip().lower()
        if not criterio_norm:
            return self.obtener_todos()

        # Búsqueda Full-Text rudimentaria por ahora.
        # En la Fase 2, esto será reemplazado por embeddings vectoriales.
        query = f"%{criterio_norm}%"
        with self._conectar() as conn:
            filas = conn.execute("""
                SELECT * FROM artistas 
                WHERE LOWER(nombre) LIKE ? 
                   OR LOWER(origen) LIKE ? 
                   OR LOWER(corriente) LIKE ? 
                   OR LOWER(instrumento) LIKE ?
            """, (query, query, query, query)).fetchall()
            return [self._fila_a_dict(f) for f in filas]

    def obtener_por_id(self, item_id: int) -> Optional[Dict]:
        with self._conectar() as conn:
            fila = conn.execute("SELECT * FROM artistas WHERE id = ?", (item_id,)).fetchone()
            return self._fila_a_dict(fila) if fila else None

    def agregar_nota(self, item_id: int, nueva_nota: str) -> bool:
        with self._conectar() as conn:
            fila = conn.execute("SELECT nota FROM artistas WHERE id = ?", (item_id,)).fetchone()
            if not fila:
                return False
            
            nota_actual = fila["nota"]
            nota_final = f"{nota_actual}\n   • {nueva_nota}" if nota_actual else f"• {nueva_nota}"
            
            conn.execute("UPDATE artistas SET nota = ? WHERE id = ?", (nota_final, item_id))
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
            return nuevo_item

