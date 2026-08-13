"""
Módulo Core: Lógica de negocio, búsqueda profunda y fusión automática entre data.py y catalogo.json.
"""

import json
import os
from typing import List, Dict, Optional


class CatalogEngine:
    """Motor de búsqueda, persistencia y sincronización de registros."""

    def __init__(self, archivo_json: str = "catalogo.json", datos_iniciales: Optional[List[Dict]] = None):
        self.archivo_json = archivo_json
        self.items = self._cargar_datos(datos_iniciales)

    def _cargar_datos(self, datos_iniciales: Optional[List[Dict]] = None) -> List[Dict]:
        """Carga los datos del JSON y fusiona por ID con registros nuevos en data.py."""
        datos_iniciales = datos_iniciales or []

        # 1. Si no existe el JSON, se genera con la semilla inicial
        if not os.path.exists(self.archivo_json):
            self._guardar_en_disco(datos_iniciales)
            return datos_iniciales

        # 2. Si existe, se lee el JSON actual
        try:
            with open(self.archivo_json, "r", encoding="utf-8") as f:
                items_json = json.load(f)
        except (json.JSONDecodeError, OSError):
            items_json = []

        # 3. Mapeo de IDs para evitar duplicar
        ids_existentes = {item["id"] for item in items_json if "id" in item}

        # 4. Fusión de nuevos registros añadidos en data.py
        hubo_cambios = False
        for artista in datos_iniciales:
            if artista.get("id") not in ids_existentes:
                items_json.append(artista)
                hubo_cambios = True

        # 5. Guardado si hubo actualizaciones
        if hubo_cambios:
            items_json.sort(key=lambda x: x.get("id", 0))
            self._guardar_en_disco(items_json)

        return items_json

    def _guardar_en_disco(self, items: Optional[List[Dict]] = None):
        """Escribe el estado actual del catálogo en el archivo JSON."""
        datos_a_guardar = items if items is not None else self.items
        with open(self.archivo_json, "w", encoding="utf-8") as f:
            json.dump(datos_a_guardar, f, ensure_ascii=False, indent=4)

    def obtener_todos(self) -> List[Dict]:
        return self.items

    def buscar(self, criterio: str) -> List[Dict]:
        """Búsqueda plana recursiva en cualquier campo (cadena, lista, entero)."""
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

    def obtener_por_id(self, item_id: int) -> Optional[Dict]:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def agregar_nota(self, item_id: int, nota: str) -> bool:
        """Agrega o actualiza una nota anexa a un artista existente."""
        item = self.obtener_por_id(item_id)
        if item:
            item["nota"] = nota
            self._guardar_en_disco()
            return True
        return False

    def agregar_item(
        self,
        nombre: str,
        origen: str,
        corriente: List[str],
        instrumento: List[str],
        tipo_agrupacion: str,
        agrupaciones_propias: List[str],
        colaboraciones_clave: List[str],
        albumes_fundamentales: List[str],
        anio_inicio: Optional[int],
        anio_fin: Optional[int],
    ) -> Dict:
        """Inserta un nuevo registro asignando ID incremental y guardando en JSON."""
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