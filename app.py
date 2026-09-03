import streamlit as st
import json
from core import CatalogEngine
import os

# Configuración inicial de la página
st.set_page_config(page_title="JazzCatalog RAG", page_icon="🎷", layout="wide")

# Inicialización de la base de datos y caché del motor RAG
@st.cache_resource(show_spinner="Inicializando modelo RAG y base de datos...")
def get_engine():
    # Intenta cargar datos iniciales si existen
    datos_iniciales = None
    if os.path.exists("data/data.py"):
        try:
            from data.data import dataset
            datos_iniciales = dataset
        except Exception:
            pass
            
    engine = CatalogEngine(datos_iniciales=datos_iniciales)
    # Validar que todo tenga sus vectores
    engine.generar_embeddings_faltantes()
    return engine

engine = get_engine()

# CSS para las Badges
st.markdown("""
<style>
.badge {
    display: inline-block; padding: 0.25em 0.4em; font-size: 75%; font-weight: 700;
    line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline;
    border-radius: 0.25rem; background-color: #17a2b8; color: white; margin-right: 5px;
}
.badge-inst { background-color: #6c757d; }
</style>
""", unsafe_allow_html=True)

st.title("🎷 JazzCatalog RAG")
st.markdown("Sistema de Búsqueda Semántica y Gestión de Catálogo Musical")

# Crear los Tabs de navegación
tab_buscar, tab_gestion = st.tabs(["🔍 Búsqueda RAG", "📝 Gestión de Catálogo"])

# ==========================================
# TAB 1: BÚSQUEDA SEMÁNTICA Y SÍNTESIS RAG
# ==========================================
with tab_buscar:
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Consulta semántica (ej. 'bajistas pioneros del jazz fusion')", "")
    with col2:
        umbral = st.slider("Umbral de Similitud", min_value=0.1, max_value=1.0, value=0.3, step=0.05)

    if query:
        resultados = engine.buscar(query, umbral)
        
        if resultados:
            st.success(f"Se encontraron {len(resultados)} artistas relevantes.")
            
            # --- SECCIÓN DE SÍNTESIS RAG (Prompt para LLM) ---
            st.subheader("💡 Síntesis RAG (Contexto Consolidado)")
            contexto_texto = f"Contexto recuperado de la base de datos de Jazz para la consulta: '{query}'\n\n"
            for r in resultados[:3]: # Tomamos el Top 3 para no saturar la ventana de contexto
                contexto_texto += f"- {r['nombre']} ({r.get('origen', 'Desconocido')}): Corrientes: {', '.join(r.get('corriente', []))}. Instrumentos: {', '.join(r.get('instrumento', []))}.\n"
            
            prompt_final = f"{contexto_texto}\nInstrucción: Utilizando exclusivamente el contexto proporcionado arriba, redacta una respuesta detallada a la consulta del usuario."
            
            with st.expander("📋 Ver/Copiar Prompt RAG para Inferencia Generativa", expanded=True):
                st.code(prompt_final, language="markdown")

            # --- VISUALIZACIÓN DE RESULTADOS ---
            st.subheader("📊 Detalles de los Resultados")
            for r in resultados:
                with st.expander(f"{r['nombre']} - Similitud: {r.get('_score', 0):.2f}"):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        # Render de badges para géneros
                        html_corrientes = "".join([f"<span class='badge'>{g}</span>" for g in r.get('corriente', [])])
                        html_instrumentos = "".join([f"<span class='badge badge-inst'>{i}</span>" for i in r.get('instrumento', [])])
                        st.markdown(f"**Estilos:** {html_corrientes}", unsafe_allow_html=True)
                        st.markdown(f"**Instrumentos:** {html_instrumentos}", unsafe_allow_html=True)
                        
                        st.write(f"**Origen:** {r.get('origen', 'N/D')} | **Actividad:** {r.get('anio_inicio', 'N/D')} - {r.get('anio_fin') or 'Presente'}")
                        if r.get("albumes_fundamentales"):
                            st.write(f"**Álbumes Clave:** {', '.join(r.get('albumes_fundamentales'))}")
                        if r.get("nota"):
                            st.info(f"**Notas:**\n{r.get('nota')}")
                    with c2:
                        st.metric(label="Cosine Score", value=f"{r.get('_score', 0):.3f}")
        else:
            st.warning("No se encontraron resultados que superen el umbral establecido.")

# ==========================================
# TAB 2: GESTIÓN DE CATÁLOGO
# ==========================================
with tab_gestion:
    st.header("Gestión del Catálogo")
    
    col_form, col_notas = st.columns(2)
    
    # Formulario de Nuevo Artista
    with col_form:
        st.subheader("Agregar Nuevo Artista")
        with st.form("form_nuevo_artista", clear_on_submit=True):
            nombre = st.text_input("Nombre del Artista*")
            origen = st.text_input("Origen (País/Ciudad)")
            corrientes = st.text_input("Corrientes (separadas por coma)")
            instrumentos = st.text_input("Instrumentos (separados por coma)")
            albumes = st.text_input("Álbumes fundamentales (separados por coma)")
            col_anios1, col_anios2 = st.columns(2)
            anio_inicio = col_anios1.number_input("Año Inicio", min_value=1800, max_value=2100, value=1950, step=1)
            anio_fin = col_anios2.number_input("Año Fin (0 = Presente)", min_value=0, max_value=2100, value=0, step=1)
            
            submit_btn = st.form_submit_button("Guardar en Catálogo")
            
            if submit_btn:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    a_fin = None if anio_fin == 0 else anio_fin
                    engine.agregar_item(
                        nombre=nombre,
                        origen=origen,
                        corriente=[x.strip() for x in corrientes.split(",") if x.strip()],
                        instrumento=[x.strip() for x in instrumentos.split(",") if x.strip()],
                        tipo_agrupacion="Solista",
                        agrupaciones_propias=[],
                        colaboraciones_clave=[],
                        albumes_fundamentales=[x.strip() for x in albumes.split(",") if x.strip()],
                        anio_inicio=anio_inicio,
                        anio_fin=a_fin
                    )
                    st.success(f"¡{nombre} agregado exitosamente e indexado semánticamente!")

    # Formulario para Agregar Notas
    with col_notas:
        st.subheader("Agregar Nota a Artista Existente")
        artistas_db = engine.obtener_todos()
        opciones = {f"{a['nombre']} (ID: {a['id']})": a['id'] for a in artistas_db}
        
        with st.form("form_notas", clear_on_submit=True):
            seleccion = st.selectbox("Seleccionar Artista", options=list(opciones.keys()))
            nueva_nota = st.text_area("Nota o apunte")
            
            submit_nota = st.form_submit_button("Añadir Nota")
            
            if submit_nota and nueva_nota.strip():
                id_seleccionado = opciones[seleccion]
                if engine.agregar_nota(id_seleccionado, nueva_nota):
                    st.success("Nota añadida exitosamente.")
                else:
                    st.error("Hubo un error al añadir la nota.")

