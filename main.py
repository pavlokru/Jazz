import sys

# Mejora la navegación de la terminal si está disponible
try:
    import readline
except ImportError:
    pass 

from cli import CatalogCLI, CatalogAPIClient

def main():
    # En la Fase 4, el engine pesadamente acoplado (CatalogEngine) se reemplaza 
    # por el cliente HTTP (CatalogAPIClient) sin que la interfaz gráfica lo note.
    # Esto reduce la huella de memoria del proceso cliente a casi cero.
    
    print("\033[2mConectando con la API Local en puerto 8000...\033[0m")
    client = CatalogAPIClient(base_url="http://127.0.0.1:8000")
    
    # Inyectamos el cliente en la CLI existente
    app = CatalogCLI(client)
    app.ejecutar()

if __name__ == "__main__":
    main()

