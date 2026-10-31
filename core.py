import sqlite3
import json
import os
from typing import Dict, List, Optional

class CatalogEngine:
    """Motor de búsqueda textual pura y persistencia SQLite optimizado para bajo footprint de RAM y CPU."""

    def __init__(self, db_path: str = None, datos_iniciales: List[Dict] = None):
        self.db_path = db_path or os.path.join(os.getcwd(), "data", "catalogo.db")
        
        self._preparar_entorno()
        self._inicializar_db()
        
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
            
            # Nota: Si usas la base de datos vieja (v2), la columna 'embedding' 
            # seguirá existiendo en el archivo .db, pero simplemente la ignoraremos.

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
        
        # Eliminamos el BLOB del dict por si estamos conectando a la DB antigua de la v2
        d.pop("embedding", None)
        return d

    def buscar(self, criterio: str) -> List[Dict]:
        """Realiza una búsqueda textual directa usando LIKE."""
        criterio_norm = criterio.strip()
        if not criterio_norm:
            return self.obtener_todos()
            
        termino = f"%{criterio_norm}%"
        
        with self._conectar() as conn:
            query = """
                SELECT * FROM artistas 
                WHERE nombre LIKE ? 
                   OR origen LIKE ? 
                   OR corriente LIKE ? 
                   OR instrumento LIKE ? 
                   OR nota LIKE ?
            """
            filas = conn.execute(query, (termino, termino, termino, termino, termino)).fetchall()
            
        return [self._fila_a_dict(f) for f in filas]

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
            # Añade la nota secuencialmente al historial existente
            nota_final = f"{nota_actual}\n\n{nueva_nota}" if nota_actual else f"• {nueva_nota}"
            
            conn.execute("UPDATE artistas SET nota = ? WHERE id = ?", (nota_final, item_id))
            conn.commit()
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
            conn.commit()
            
        return nuevo_item

    def eliminar_artista(self, artist_id: int) -> bool:
        """Elimina un artista de la base de datos SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute("DELETE FROM artistas WHERE id = ?", (artist_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar artista ID {artist_id}: {e}")
            return False