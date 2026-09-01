import json
import urllib.request
import urllib.parse
from urllib.error import URLError
import textwrap
from typing import Dict, List, Optional

# --- ADAPTADOR DE API LOCAL (FASE 4) ---
# Ocupa < 15MB de RAM. Toda la inferencia IA ocurre en el daemon uvicorn.

class CatalogAPIClient:
    """Cliente HTTP ultraliviano basado en la librería estándar."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def _hacer_peticion(self, metodo: str, path: str, params: Optional[dict] = None, payload: Optional[dict] = None):
        url = f"{self.base_url}{path}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"

        headers = {"User-Agent": "JazzCatalogCLI/2.0"}
        data = None

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=metodo)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except URLError:
            print("\n\033[91m⚠️ Error: No se pudo conectar con la API local (127.0.0.1:8000).\033[0m")
            print("\033[2mAsegúrate de tener corriendo 'uvicorn api:app' en otra terminal.\033[0m\n")
            return None

    def obtener_todos(self) -> List[Dict]:
        res = self._hacer_peticion("GET", "/catalogo")
        return res if res is not None else []

    def buscar(self, criterio: str) -> List[Dict]:
        res = self._hacer_peticion("GET", "/buscar", params={"q": criterio})
        return res if res is not None else []

    def obtener_por_id(self, item_id: int) -> Optional[Dict]:
        return self._hacer_peticion("GET", f"/catalogo/{item_id}")

    def agregar_nota(self, item_id: int, nueva_nota: str) -> bool:
        res = self._hacer_peticion("POST", f"/catalogo/{item_id}/nota", payload={"nota": nueva_nota})
        return bool(res and res.get("status") == "ok")

    def agregar_item(self, **kwargs) -> Dict:
        res = self._hacer_peticion("POST", "/catalogo", payload=kwargs)
        return res if res is not None else {}


# --- INTERFAZ GRÁFICA DE CONSOLA (CLI) ---

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
DIM = "\033[2m"
RED = "\033[91m"

class CatalogCLI:
    def __init__(self, motor):
        self.motor = motor
        self.ancho = 38  # Optimizado para terminales móviles

    def _print_header(self, titulo: str):
        print(f"\n{CYAN}{BOLD}{titulo.center(self.ancho)}{RESET}")
        print(f"{CYAN}{'=' * self.ancho}{RESET}")

    def _print_wrap(self, texto: str, color: str = ""):
        lineas = textwrap.wrap(texto, width=self.ancho)
        for linea in lineas:
            print(f"{color}{linea}{RESET}")

    def _imprimir_ficha(self, d: Dict):
        print(f"\n{GREEN}{BOLD}ID: {d.get('id')} - {d.get('nombre')}{RESET}")
        if "_score" in d:
            print(f"{YELLOW}Similitud: {d['_score']:.4f}{RESET}")
        
        if d.get("origen"): print(f"{BOLD}Origen:{RESET} {d['origen']}")
        if d.get("anio_inicio"): 
            fin = d.get("anio_fin") or "Presente"
            print(f"{BOLD}Período:{RESET} {d['anio_inicio']} - {fin}")
        if d.get("corriente"): print(f"{BOLD}Corrientes:{RESET} {', '.join(d['corriente'])}")
        if d.get("instrumento"): print(f"{BOLD}Instrumentos:{RESET} {', '.join(d['instrumento'])}")
        if d.get("tipo_agrupacion"): print(f"{BOLD}Formato:{RESET} {d['tipo_agrupacion']}")
        
        if d.get("agrupaciones_propias"):
            print(f"{BOLD}Proyectos Propios:{RESET}")
            for i in d["agrupaciones_propias"]: print(f"  • {i}")
            
        if d.get("colaboraciones_clave"):
            print(f"{BOLD}Colaboraciones:{RESET}")
            for i in d["colaboraciones_clave"]: print(f"  • {i}")
            
        if d.get("albumes_fundamentales"):
            print(f"{BOLD}Álbumes Clave:{RESET}")
            for i in d["albumes_fundamentales"]: print(f"  • {i}")
            
        if d.get("nota"):
            print(f"\n{MAGENTA}{BOLD}--- NOTAS ---{RESET}")
            self._print_wrap(d["nota"], MAGENTA)
        
        print(f"{DIM}{'-' * self.ancho}{RESET}")

    def ejecutar(self):
        while True:
            self._print_header("CATÁLOGO DE JAZZ")
            print("1. Ver todos los artistas")
            print("2. Búsqueda semántica (RAG)")
            print("3. Ver ficha completa por ID")
            print("4. Agregar nota a un artista")
            print("5. Salir")
            
            opcion = input(f"\n{BOLD}Elige una opción:{RESET} ").strip()
            
            if opcion == '1':
                self._menu_todos()
            elif opcion == '2':
                self._menu_buscar()
            elif opcion == '3':
                self._menu_ficha()
            elif opcion == '4':
                self._menu_nota()
            elif opcion == '5':
                print(f"\n{YELLOW}Saliendo del cliente...{RESET}")
                break
            else:
                print(f"{RED}Opción no válida.{RESET}")

    def _menu_todos(self):
        self._print_header("TODOS LOS ARTISTAS")
        resultados = self.motor.obtener_todos()
        if not resultados:
            print(f"{YELLOW}El catálogo está vacío o el motor no responde.{RESET}")
            return
        for item in resultados:
            print(f"{BOLD}[{item['id']}]{RESET} {item['nombre']} {DIM}({item.get('origen', '')}){RESET}")
        print(f"\n{DIM}Total: {len(resultados)} registros.{RESET}")

    def _menu_buscar(self):
        self._print_header("BÚSQUEDA SEMÁNTICA")
        criterio = input("Término de búsqueda:\n> ").strip()
        if not criterio:
            return
        print(f"{DIM}Consultando a la API...{RESET}")
        resultados = self.motor.buscar(criterio)
        if not resultados:
            print(f"{YELLOW}No se encontraron coincidencias.{RESET}")
        else:
            for item in resultados:
                self._imprimir_ficha(item)

    def _menu_ficha(self):
        self._print_header("BUSCAR POR ID")
        try:
            item_id = int(input("ID del artista: ").strip())
            item = self.motor.obtener_por_id(item_id)
            if item:
                self._imprimir_ficha(item)
            else:
                print(f"{RED}No se pudo recuperar el artista (ID {item_id}).{RESET}")
        except ValueError:
            print(f"{RED}ID inválido. Debe ser un número.{RESET}")

    def _menu_nota(self):
        self._print_header("AGREGAR NOTA")
        try:
            item_id = int(input("ID del artista: ").strip())
            item = self.motor.obtener_por_id(item_id)
            if not item:
                print(f"{RED}No existe artista con ID {item_id}{RESET}")
                return
            print(f"Agregando nota a: {GREEN}{item['nombre']}{RESET}")
            nota = input("Escribe tu nota (presiona Enter al terminar):\n> ").strip()
            if nota:
                exito = self.motor.agregar_nota(item_id, nota)
                if exito:
                    print(f"{GREEN}Nota guardada con éxito.{RESET}")
                else:
                    print(f"{RED}Error al guardar la nota.{RESET}")
        except ValueError:
            print(f"{RED}ID inválido. Debe ser un número.{RESET}")

