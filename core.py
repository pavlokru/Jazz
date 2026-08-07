"""
Módulo Core: Lógica de negocio, búsqueda profunda y fusión automática entre data.py y catalogo.json.
"""

import json
import os


class CatalogEngine:
    """Motor de búsqueda y persistencia para el catálogo enriquecido de jazzistas."""

    def __init__(
        self, archivo_json: str = "catalogo.json", datos_iniciales: list[dict] = None
    ):
        self.archivo_json = archivo_json
        self.items = self._cargar_datos(datos_iniciales)

    def _cargar_datos(self, datos_iniciales: list[dict] = None) -> list[dict]:
        """
        Carga datos del JSON y los fusiona con los nuevos registros de data.py si existen.
        """
        datos_iniciales = datos_iniciales or []

        # 1. Si no existe el archivo JSON, creamos con los datos iniciales y guardamos
        if not os.path.exists(self.archivo_json):
            self._guardar_en_disco(datos_iniciales)
            return datos_iniciales

        # 2. Si el archivo existe, leemos lo que tiene actualmente
        try:
            with open(self.archivo_json, "r", encoding="utf-8") as f:
                items_json = json.load(f)
        except (json.JSONDecodeError, OSError):
            items_json = []

        # 3. Mapeamos los IDs existentes en el JSON para evitar duplicados
        ids_existentes = {item["id"] for item in items_json if "id" in item}

        # 4. Buscamos si hay registros en data.py que NO estén en el JSON
        hubo_cambios = False
        for artista in datos_iniciales:
            if artista.get("id") not in ids_existentes:
                items_json.append(artista)
                hubo_cambios = True

        # 5. Si encontramos nuevos artistas en data.py, actualizamos catalogo.json
        if hubo_cambios:
            # Ordenamos por ID para mantener consistencia
            items_json.sort(key=lambda x: x.get("id", 0))
            self._guardar_en_disco(items_json)

        return items_json

    def _guardar_en_disco(self, items: list[dict] = None):
        """Persiste el estado actual en el archivo JSON."""
        datos_a_guardar = items if items is not None else self.items
        with open(self.archivo_json, "w", encoding="utf-8") as f:
            json.dump(datos_a_guardar, f, ensure_ascii=False, indent=4)

    def obtener_todos(self) -> list[dict]:
        return self.items

    def buscar(self, criterio: str) -> list[dict]:
        """Búsqueda plana sobre cadenas, listas de strings y enteros."""
        criterio_norm = criterio.strip().lower()
        if not criterio_norm:
            return self.items

        resultados = []
        for item in self.items:
            buffer_texto = []
            for val in item.values():
                if isinstance(val, list):
                    buffer_texto.append(" ".join(str(v) for v in val))
                elif val is not None:
                    buffer_texto.append(str(val))

            texto_completo = " ".join(buffer_texto).lower()
            if criterio_norm in texto_completo:
                resultados.append(item)
        return resultados

    def obtener_por_id(self, item_id: int) -> dict | None:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def agregar_item(
        self,
        nombre: str,
        origen: str,
        corriente: list[str],
        instrumento: list[str],
        tipo_agrupacion: str,
        agrupaciones_propias: list[str],
        colaboraciones_clave: list[str],
        albumes_fundamentales: list[str],
        anio_inicio: int | None,
        anio_fin: int | None,
    ) -> dict:
        """Genera ID e inserta un nuevo registro desde el CLI guardándolo en disco."""
        nuevo_id = max([item["id"] for item in self.items], default=0) + 1
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
        }
        self.items.append(nuevo_item)
        self._guardar_en_disco()
        return nuevo_item
