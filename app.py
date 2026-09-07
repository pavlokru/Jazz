import os
import torch

# Capturar RuntimeError si Streamlit reejecuta el script en el mismo proceso
try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

# 1. Ajuste estricto de hilos para evitar límites de CPU en Streamlit Cloud
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
import json
from core import CatalogEngine

# Configuración de página
st.set_page_config(
    page_title="JazzCatalog RAG",
    page_icon="🎷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para Badges y Tarjetas
st.markdown("""
<style>
    .badge-corriente {
        display: inline-block; padding: 3px 8px; font-size: 12px; font-weight: 600;
        border-radius: 12px; background-color: #2b5c8f; color: #ffffff;
        margin-right: 4px; margin-bottom: 4px;
    }
    .badge-inst {
        display: inline-block; padding: 3px 8px; font-size: 12px; font-weight: 600;
        border-radius: 12px; background-color: #4a5568; color: #ffffff;
        margin-right: 4px; margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Cargando motor RAG y base de datos...")
def obtener_motor():
    datos_iniciales = None
    if os.path.exists("data/data.py"):
        try:
            from data.data import dataset
            datos_iniciales = dataset
        except Exception:
            pass
            
    engine = CatalogEngine(datos_iniciales=datos_iniciales)
    engine.generar_embeddings_faltantes()
    return engine


engine = obtener_motor()

# ==========================================
# BARRA LATERAL (Métricas y Filtros)
# ==========================================
with st.sidebar:
    st.header("🎷 JazzCatalog")
    st.caption("Sistema Semantic RAG v2.0")
    st.divider()
    
    todos_artistas = engine.obtener_todos()
    total_artistas = len(todos_artistas)
    
    corrientes_unicas = set()
    instrumentos_unicos = set()
    for a in todos_artistas:
        corrientes_unicas.update(a.get("corriente", []))
        instrumentos_unicos.update(a.get("instrumento", []))
        
    st.metric(label="Total Artistas", value=total_artistas)
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label="Estilos", value=len(corrientes_unicas))
    col_m2.metric(label="Instrumentos", value=len(instrumentos_unicos))


# ==========================================
# ESTRUCTURA PRINCIPAL DE NAVEGACIÓN
# ==========================================
st.title("🎷 JazzCatalog RAG")
st.markdown("Búsqueda semántica vectorial y gestión avanzada del catálogo de jazz.")

tab_rag, tab_explorador, tab_gestion = st.tabs([
    "🔍 Búsqueda RAG", 
    "📚 Explorador Completo", 
    "📝 Gestión del Catálogo"
])


# ------------------------------------------
# TAB 1: BÚSQUEDA SEMÁNTICA (Se mantiene igual)
# ------------------------------------------
with tab_rag:
    col_q, col_u = st.columns([3, 1])
    with col_q:
        query = st.text_input("Consulta en lenguaje natural", placeholder="Ej: Pioneros del Latin Jazz y Bebop de Cuba", key="input_query")
    with col_u:
        umbral = st.slider("Umbral de Similitud", min_value=0.1, max_value=0.9, value=0.3, step=0.05)

    if query.strip():
        resultados = engine.buscar(query, umbral=umbral)
        if resultados:
            st.subheader(f"Resultados Encontrados ({len(resultados)})")
            # Renderizado RAG omitido aquí por brevedad, se mantiene tu código de la Fase 1.
            # Puedes conservar la lógica de la Tab 1 exacta que tenías antes.
            for res in resultados:
                with st.expander(f"{res['nombre']} - Similitud: {res.get('_score', 0):.3f}"):
                    st.write(f"**Origen:** {res.get('origen')} | **Estilos:** {', '.join(res.get('corriente', []))}")
                    if res.get("nota"):
                        st.info(res.get("nota"))
        else:
            st.warning("No se encontraron coincidencias.")


# ------------------------------------------
# TAB 2: EXPLORADOR COMPLETO (Actualizado al nuevo esquema)
# ------------------------------------------
# ------------------------------------------
# TAB 2: EXPLORador COMPLETO (Con Filtro Amplio)
# ------------------------------------------
with tab_explorador:
    st.subheader("Directorio de Artistas")
    
    # Nuevo filtro amplio
    filtro_texto = st.text_input(
        "🔍 Buscar por nombre, origen, estilo o instrumento", 
        placeholder="Ej: Cuba, Trompeta, Bebop..."
    )
    
    artistas_filtrados = todos_artistas
    if filtro_texto.strip():
        f = filtro_texto.lower()
        artistas_filtrados = [
            a for a in todos_artistas 
            if f in str(a.get('nombre', '')).lower() 
            or f in str(a.get('origen', '')).lower()
            or any(f in str(c).lower() for c in a.get('corriente', []))
            or any(f in str(i).lower() for i in a.get('instrumento', []))
        ]
        
    st.caption(f"Mostrando {len(artistas_filtrados)} resultados.")
    
    for art in artistas_filtrados:
        with st.expander(f"👤 {art['nombre']} ({art.get('origen', 'Origen N/D')})"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Tipo de Agrupación:** {art.get('tipo_agrupacion', 'N/D')}")
                st.write(f"**Corrientes:** {', '.join(art.get('corriente', []))}")
                st.write(f"**Instrumentos:** {', '.join(art.get('instrumento', []))}")
                st.write(f"**Agrupaciones Propias:** {', '.join(art.get('agrupaciones_propias', []))}")
            with c2:
                st.write(f"**Colaboraciones Clave:** {', '.join(art.get('colaboraciones_clave', []))}")
                st.write(f"**Álbumes Fundamentales:** {', '.join(art.get('albumes_fundamentales', []))}")
                st.write(f"**Período de Actividad:** {art.get('anio_inicio', 'N/D')} - {art.get('anio_fin') or 'Presente'}")
            
            if art.get("nota"):
                st.info(f"**Biografía / Notas:**\n\n{art.get('nota')}")


# ------------------------------------------
# TAB 3: GESTIÓN DE CATÁLOGO (Actualizado al nuevo esquema)
# ------------------------------------------
with tab_gestion:
    col_add, col_note = st.columns([1.2, 0.8])
    
    # Formulario: Agregar nuevo artista (Esquema Completo)
    with col_add:
        st.subheader("Añadir Registro (Perfil Completo)")
        with st.form("form_nuevo_artista_v3", clear_on_submit=True):
            nombre = st.text_input("Nombre completo del artista / banda*")
            origen = st.text_input("Origen (País, Ciudad)")
            
            c_t1, c_t2 = st.columns(2)
            tipo_agrupacion = c_t1.text_input("Tipo de agrupación (Ej: Solista, Quinteto)")
            agrupaciones_raw = c_t2.text_input("Agrupaciones propias (separadas por comas)")
            
            corriente_raw = st.text_input("Corrientes (separadas por comas)")
            instrumento_raw = st.text_input("Instrumentos (separados por comas)")
            colabs_raw = st.text_input("Colaboraciones clave (separadas por comas)")
            albumes_raw = st.text_area("Álbumes fundamentales (separados por comas)")
            
            c_a1, c_a2 = st.columns(2)
            anio_inicio = c_a1.number_input("Año inicio", min_value=1800, max_value=2100, value=1970)
            anio_fin = c_a2.number_input("Año fin (0 si sigue activo)", min_value=0, max_value=2100, value=0)
            
            # Incorporación directa de la nota biográfica en la creación
            nota_biografica = st.text_area("Nota biográfica / Apunte histórico (Opcional)", height=150)
            
            btn_guardar = st.form_submit_button("Guardar Perfil e Indexar")
            
            if btn_guardar:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    # Limpieza y conversión a listas
                    lista_corriente = [x.strip() for x in corriente_raw.split(",") if x.strip()]
                    lista_instrumento = [x.strip() for x in instrumento_raw.split(",") if x.strip()]
                    lista_agrup = [x.strip() for x in agrupaciones_raw.split(",") if x.strip()]
                    lista_colabs = [x.strip() for x in colabs_raw.split(",") if x.strip()]
                    lista_albumes = [x.strip() for x in albumes_raw.split(",") if x.strip()]
                    
                    a_fin = None if anio_fin == 0 else int(anio_fin)
                    
                    # 1. Crear el artista básico
                    nuevo_item = engine.agregar_item(
                        nombre=nombre.strip(),
                        origen=origen.strip(),
                        corriente=lista_corriente,
                        instrumento=lista_instrumento,
                        tipo_agrupacion=tipo_agrupacion.strip(),
                        agrupaciones_propias=lista_agrup,
                        colaboraciones_clave=lista_colabs,
                        albumes_fundamentales=lista_albumes,
                        anio_inicio=int(anio_inicio),
                        anio_fin=a_fin
                    )
                    
                    # 2. Si se incluyó nota, se agrega usando el método de core.py y se actualiza el vector
                    if nota_biografica.strip():
                        engine.agregar_nota(nuevo_item["id"], nota_biografica.strip())
                        # Forzamos la re-vectorización manual para incluir la nota en el embedding
                        engine.generar_embeddings_faltantes() 
                        
                    st.toast(f"¡{nombre} registrado exitosamente con perfil completo!", icon="✅")
                    st.rerun()

    # Formulario: Agregar notas adicionales a artista existente
    with col_note:
        st.subheader("Añadir Apuntes Adicionales")
        
        opciones_artistas = {f"{a['nombre']} (ID: {a['id']})": a['id'] for a in todos_artistas}
        
        if opciones_artistas:
            with st.form("form_agregar_nota_v3", clear_on_submit=True):
                seleccionado = st.selectbox("Seleccionar artista", options=list(opciones_artistas.keys()))
                nueva_nota = st.text_area("Nuevo apunte o actualización")
                
                btn_nota = st.form_submit_button("Guardar Nota")
                
                if btn_nota and nueva_nota.strip():
                    artist_id = opciones_artistas[seleccionado]
                    if engine.agregar_nota(artist_id, nueva_nota.strip()):
                        # Al añadir una nota, los datos cambian, forzamos re-indexación
                        engine.generar_embeddings_faltantes()
                        st.toast("Nota agregada correctamente", icon="📌")
                        st.rerun()
                    else:
                        st.error("Error al guardar la nota.")
        else:
            st.info("El catálogo está vacío.")


# ------------------------------------------
# TAB 3: GESTIÓN DE CATÁLOGO (Agregar botón de backup)
# ------------------------------------------
with tab_gestion:
    
    # ... (Tu código existente de los formularios form_nuevo_artista_v3 y form_agregar_nota_v3) ...

    st.divider()
    
    # Nueva sección de Respaldos
    st.subheader("💾 Respaldo de Base de Datos")
    st.info("Descarga la base de datos SQLite actualizada para resguardar los últimos embeddings generados o sincronizar tu entorno local.")
    
    db_path = "data/catalogo.db"
    
    # Verificamos que el archivo exista antes de ofrecer la descarga
    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.download_button(
                label="⬇️ Descargar catalogo.db",
                data=f,
                file_name="catalogo.db",
                mime="application/octet-stream",
                use_container_width=True
            )
    else:
        st.warning("El archivo de base de datos aún no se ha creado.")

