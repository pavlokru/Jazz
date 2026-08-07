"""
Punto de Entrada: Instancia el motor con el catálogo de data.py y lanza la interfaz CLI.
"""

from data import CATALOGO_JAZZ
from core import CatalogEngine
from cli import CatalogCLI


def main():
    engine = CatalogEngine(archivo_json="catalogo.json", datos_iniciales=CATALOGO_JAZZ)
    app = CatalogCLI(engine)
    app.ejecutar()


if __name__ == "__main__":
    main()
