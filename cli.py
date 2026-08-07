"""
Módulo CLI: Interfaz optimizada para pantallas verticales de celular (Ancho max: 38 cols).
"""

from core import CatalogEngine

# Códigos ANSI para formato y color
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
DIM = "\033[2m"


class CatalogCLI:
    """Maneja la presentación visual ajustada a formato vertical móvil."""

    def __init__(self, engine: CatalogEngine):
        self.engine = engine

    def _separador(self):
        print(f"{DIM}{'─' * 38}{RESET}")

    def mostrar_menu(self):
        print(f"\n{CYAN}┌────────────────────────────────────┐{RESET}")
        print(
            f"{CYAN}│{BOLD}{MAGENTA}        🎷 JAZZ CATALOG CLI         {RESET}{CYAN}│{RESET}"
        )
        print(f"{CYAN}└────────────────────────────────────┘{RESET}")
        print(f" {GREEN}[1]{RESET} {BOLD}Ver catálogo{RESET}")
        print(f" {GREEN}[2]{RESET} {BOLD}Buscar artista / estilo{RESET}")
        print(f" {GREEN}[3]{RESET} {BOLD}Ver ficha de artista{RESET}")
        print(f" {GREEN}[4]{RESET} {BOLD}Agregar nuevo artista{RESET}")
        print(f" {GREEN}[5]{RESET} {BOLD}Salir{RESET}")
        self._separador()

    def mostrar_tarjetas(self, items: list[dict]):
        """Muestra los resultados en formato de lista/tarjetas verticales compactas."""
        if not items:
            print(f"{RED}⚠️  Sin resultados.{RESET}\n")
            return

        for item in items:
            inst_str = (
                ", ".join(item.get("instrumento", []))
                if isinstance(item.get("instrumento"), list)
                else str(item.get("instrumento", ""))
            )
            corr_str = (
                ", ".join(item.get("corriente", []))
                if isinstance(item.get("corriente"), list)
                else str(item.get("corriente", ""))
            )

            print(
                f"{YELLOW}#{item['id']}{RESET} | {BOLD}{CYAN}{item['nombre'][:28]}{RESET}"
            )
            print(f"   {BLUE}Origen:{RESET} {item.get('origen', 'N/A')}")
            print(f"   {GREEN}Inst:{RESET} {inst_str[:28]}")
            print(f"   {MAGENTA}Estilo:{RESET} {corr_str[:26]}")
            self._separador()

        print(f"{GREEN}✓ Total mostrados: {len(items)}{RESET}\n")

    def mostrar_ficha(self, item: dict):
        """Ficha detallada adaptada a 38 columnas de ancho."""
        fin_str = str(item["anio_fin"]) if item.get("anio_fin") else "Presente"
        actividad = f"{item.get('anio_inicio', 'N/A')} - {fin_str}"
        inst_str = (
            ", ".join(item.get("instrumento", []))
            if isinstance(item.get("instrumento"), list)
            else str(item.get("instrumento", ""))
        )
        corr_str = (
            ", ".join(item.get("corriente", []))
            if isinstance(item.get("corriente"), list)
            else str(item.get("corriente", ""))
        )

        print(f"\n{CYAN}┌────────────────────────────────────┐{RESET}")
        print(
            f"{CYAN}│{RESET} {BOLD}{MAGENTA}FICHA #{item['id']} - {item['nombre'][:21].upper():<21}{RESET} {CYAN}│{RESET}"
        )
        print(f"{CYAN}└────────────────────────────────────┘{RESET}")
        print(f" {BLUE}• Nombre:{RESET} {BOLD}{item['nombre']}{RESET}")
        print(f" {BLUE}• Origen:{RESET} {item.get('origen', 'N/A')}")
        print(f" {BLUE}• Período:{RESET} {YELLOW}{actividad}{RESET}")
        print(f" {BLUE}• Instrumento(s):{RESET}\n   {GREEN}{inst_str}{RESET}")
        print(f" {BLUE}• Corriente(s):{RESET}\n   {MAGENTA}{corr_str}{RESET}")
        print(
            f" {BLUE}• Tipo Agrupación:{RESET}\n   {item.get('tipo_agrupacion', 'N/A')}"
        )

        print(f"\n {BOLD}{CYAN}👥 Agrupaciones:{RESET}")
        for g in item.get("agrupaciones_propias", []):
            print(f"   - {g}")

        print(f"\n {BOLD}{CYAN}🤝 Colaboraciones:{RESET}")
        for c in item.get("colaboraciones_clave", []):
            print(f"   - {c}")

        print(f"\n {BOLD}{CYAN}💿 Álbumes Clave:{RESET}")
        for alb in item.get("albumes_fundamentales", []):
            print(f"   - {alb}")

        self._separador()

    def ejecutar(self):
        while True:
            self.mostrar_menu()
            opcion = input(f"{BOLD}Opción (1-5): {RESET}").strip()

            if opcion == "1":
                print(f"\n{BOLD}{GREEN}─── 🎷 CATÁLOGO COMPLETO ───{RESET}")
                self._separador()
                self.mostrar_tarjetas(self.engine.obtener_todos())

            elif opcion == "2":
                criterio = input(f"\n{BOLD}Buscar texto: {RESET}").strip()
                items = self.engine.buscar(criterio)
                print(f"\n{BOLD}{GREEN}─── 🔍 RESULTADOS ('{criterio}') ───{RESET}")
                self._separador()
                self.mostrar_tarjetas(items)

            elif opcion == "3":
                try:
                    art_id = int(input(f"\n{BOLD}ID de artista: {RESET}").strip())
                    item = self.engine.obtener_por_id(art_id)
                    if item:
                        self.mostrar_ficha(item)
                    else:
                        print(f"{RED}⚠️ ID #{art_id} no encontrado.{RESET}\n")
                except ValueError:
                    print(f"{RED}⚠️ Ingrese un ID numérico.{RESET}\n")

            elif opcion == "4":
                print(f"\n{BOLD}{GREEN}─── ➕ NUEVO ARTISTA ───{RESET}")
                nombre = input(f"{BOLD}Nombre: {RESET}").strip()
                origen = input(f"{BOLD}Origen: {RESET}").strip()

                corriente_raw = input(f"{BOLD}Estilos (sep por coma): {RESET}").strip()
                corriente = [c.strip() for c in corriente_raw.split(",") if c.strip()]

                inst_raw = input(f"{BOLD}Instrumentos (sep por coma): {RESET}").strip()
                instrumento = [i.strip() for i in inst_raw.split(",") if i.strip()]

                tipo_agrupacion = input(f"{BOLD}Tipo Agrupación: {RESET}").strip()

                agr_raw = input(f"{BOLD}Agrup. Propias (sep por coma): {RESET}").strip()
                agrupaciones_propias = [
                    a.strip() for a in agr_raw.split(",") if a.strip()
                ]

                col_raw = input(f"{BOLD}Colaboraciones (sep por coma): {RESET}").strip()
                colaboraciones_clave = [
                    c.strip() for c in col_raw.split(",") if c.strip()
                ]

                alb_raw = input(f"{BOLD}Álbumes (sep por coma): {RESET}").strip()
                albumes_fundamentales = [
                    a.strip() for a in alb_raw.split(",") if a.strip()
                ]

                try:
                    inicio_in = input(f"{BOLD}Año inicio: {RESET}").strip()
                    anio_inicio = int(inicio_in) if inicio_in else None

                    fin_in = input(f"{BOLD}Año fin (vacío si activo): {RESET}").strip()
                    anio_fin = int(fin_in) if fin_in else None
                except ValueError:
                    print(f"{RED}⚠️ Los años deben ser números.{RESET}\n")
                    continue

                if nombre:
                    nuevo_item = self.engine.agregar_item(
                        nombre=nombre,
                        origen=origen,
                        corriente=corriente,
                        instrumento=instrumento,
                        tipo_agrupacion=tipo_agrupacion,
                        agrupaciones_propias=agrupaciones_propias,
                        colaboraciones_clave=colaboraciones_clave,
                        albumes_fundamentales=albumes_fundamentales,
                        anio_inicio=anio_inicio,
                        anio_fin=anio_fin,
                    )
                    print(
                        f"\n{GREEN}💾 ¡{nuevo_item['nombre']} guardado con ID #{nuevo_item['id']}!{RESET}\n"
                    )
                else:
                    print(f"\n{RED}⚠️ El nombre no puede estar vacío.{RESET}\n")

            elif opcion == "5":
                print(f"\n{BOLD}{GREEN}¡Hasta luego! 🎷🎶{RESET}\n")
                break
            else:
                print(f"{RED}⚠️ Opción inválida.{RESET}\n")
