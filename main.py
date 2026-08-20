"""
Punto de Entrada: Instancia el motor con el catálogo de data.py y lanza la interfaz CLI.
"""

import sys

# Activa la navegación con flechas en la consola para sistemas POSIX (Linux/Android/macOS)
try:
    import readline
except ImportError:
    pass  # En Windows readline no existe por defecto, pero tampoco suele necesitarlo



from data import CATALOGO_JAZZ
from core import CatalogEngine
from cli import CatalogCLI


def main():
    # Eliminamos archivo_json. Redirigimos a SQLite en la carpeta data/
    engine = CatalogEngine(db_path="data/catalogo.db", datos_iniciales=CATALOGO_JAZZ)
    app = CatalogCLI(engine)
    app.ejecutar()


if __name__ == "__main__":
    main()
