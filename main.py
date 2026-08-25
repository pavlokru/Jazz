import sys

# Activa la navegación con flechas en la consola para sistemas POSIX (Linux/Android/macOS)
try:
    import readline
except ImportError:
    pass 

from data import CATALOGO_JAZZ
from core import CatalogEngine
from cli import CatalogCLI

def main():
    # Instanciamos el motor conectado a SQLite
    engine = CatalogEngine(db_path="data/catalogo.db", datos_iniciales=CATALOGO_JAZZ)
    
    # Rutina de pre-arranque para la Fase 2: 
    # Asegura que todos los registros tengan su representación vectorial generada.
    print("\n\033[2mIniciando comprobación del motor de IA...\033[0m")
    nuevos_indexados = engine.generar_embeddings_faltantes()
    if nuevos_indexados > 0:
        print(f"\033[92m✓ {nuevos_indexados} registros indexados semánticamente.\033[0m")
    
    # Lanzamos el loop de la CLI que consumirá el motor adaptado
    app = CatalogCLI(engine)
    app.ejecutar()


if __name__ == "__main__":
    main()

