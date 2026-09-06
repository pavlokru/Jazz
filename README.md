JazzCatalog RAG 🎷
JazzCatalog RAG es una solución de gestión de catálogos musicales y búsqueda semántica (Retrieval-Augmented Generation) orientada al género jazz. El proyecto nació bajo la filosofía de ultraportabilidad e independencia técnica, diseñado originalmente para ejecutarse dentro de entornos con recursos de hardware ajustados (dispositivos ARM64/Android mediante Termux) y evolucionó gradualmente hasta convertirse en una plataforma web interactiva desplegable en la nube mediante Streamlit Cloud.
🏛️ Arquitectura del Sistema
El ecosistema está construido en Python 3 sobre una arquitectura por capas modular y desacoplada:

📄 Módulos Principales
 * data/data.py (Semilla de Datos): Contiene la estructura de datos enriquecida inicial (CATALOGO_JAZZ) con atributos como corrientes, instrumentos, agrupaciones, colaboraciones y notas biográficas.
 * core.py (Motor RAG y Persistencia): Administra las transacciones SQL sobre catalogo.db, la instanciación perezosa (lazy loading) del modelo de vectorización y el motor de búsqueda vectorial matricial.
 * app.py (Interfaz Gráfica Principal): Aplicación interactiva multilengueta desarrollada en Streamlit para la exploración visual, consultas semánticas en lenguaje natural y gestión del catálogo.
 * cli.py / main.py (Cliente TUI - Opcional): Interfaz CLI alternativa formateada para pantallas reducidas de hasta 38 columnas de ancho.
🛠️ Especificaciones Técnicas y Rendimiento
 * Base de Datos Persistente: SQLite (catalogo.db) para almacenar metadatos JSON y vectores guardados en formato binario BLOB (np.float32).
 * Modelo de Embeddings: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones).
 * Carga Perezosa (Lazy Loading): El modelo de SentenceTransformers solo se carga en memoria al realizar la primera inferencia o indexación.
 * Cálculo de Similitud Coseno: Procesamiento de producto punto normalizado directo con NumPy sin sobrecargar la RAM.
 * Optimización de Recurso CPU: Implementación de límites estrictos de hilos (torch.set_num_threads(1) y variables de entorno C/C++) para evitar penalizaciones (throttling) en entornos cloud con recursos compartidos.
🚀 Instalación y Uso
1. Requisitos Previos
 * Python 3.9 o superior.
 * Git.
2. Clonar el Repositorio e Instalar Dependencias
git clone https://github.com/tu-usuario/jazzcatalog-rag.git
cd jazzcatalog-rag

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Linux/macOS
# .venv\Scripts\activate   # En Windows

# Instalar librerías
pip install -r requirements.txt

3. Ejecutar la Aplicación
Interfaz Web con Streamlit:
streamlit run app.py

Interfaz CLI en Terminal (38 columnas):
python main.py

📁 Esquema de Datos (Dataset)
Cada registro dentro del catálogo se encuentra normalizado bajo la siguiente estructura:
{
    "id": 1,
    "nombre": "Arturo Sandoval",
    "origen": "Artemisa, Cuba",
    "corriente": ["Afro-Cuban Jazz", "Latin Jazz", "Bebop"],
    "instrumento": ["Trompeta", "Fliscorno", "Piano"],
    "tipo_agrupacion": "Solista / Quinteto",
    "agrupaciones_propias": ["Arturo Sandoval & His Band", "Irakere"],
    "colaboraciones_clave": ["Dizzy Gillespie", "Chucho Valdés", "Paquito D'Rivera"],
    "albumes_fundamentales": ["Flight to Freedom (1991)", "I Remember Clifford (1992)"],
    "anio_inicio": 1964,
    "anio_fin": null,
    "nota": "Pionero fundamental del Latin Jazz y cofundador de Irakere..."
}

⚡ Estrategia de Despliegue en la Nube (Streamlit Cloud)
Para prevenir bloqueos por alto uso de CPU durante el arranque en la nube:
 * Genera localmente el archivo data/catalogo.db pre-vectorizado ejecutando la app en tu máquina local.
 * Incluye data/catalogo.db en los cambios del repositorio (git add data/catalogo.db).
 * Al iniciar en la nube, el motor detectará los embeddings existentes y omitirá la fase intensiva de re-vectorización.
