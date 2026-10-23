# TikTok Web Scraper & Semantic Profile Analyzer (Playwright + Hugging Face)

Sistema automatizado de extracción de datos y análisis semántico para perfiles públicos de TikTok en Python. Opera sin depender de APIs externas de pago ni librerías de scraping de terceros, combinando intercepción de tráfico de red con modelos de lenguaje (*Embeddings*) de Hugging Face.

---

## Arquitectura del Sistema

1. **Extracción Híbrida (`scraper_tiktok.py`):**
   - **Estado de Hidratación (`#__UNIVERSAL_DATA_FOR_REHYDRATION__`):** Extrae directamente del árbol JSON del servidor los metadatos exactos del perfil (`username`, `nombre`, `biografia`, `seguidores`, `total_publicaciones`), evitando el redondeo visual de la interfaz web.
   - **Intercepción Asíncrona XHR/Fetch (`/api/post/item_list/`):** Captura en segundo plano (`page.on("response")`) los paquetes JSON con las métricas reales de las últimas 10 publicaciones (`video_id`, `fecha_timestamp`, `likes`, `comentarios`, `compartidos`).
2. **Clasificación Semántica con IA (`analizar_embeddings.py`):**
   - Implementa el modelo **`sentence-transformers/all-MiniLM-L6-v2`** de Hugging Face para vectorizar el contenido textual del perfil (384 dimensiones).
   - Calcula la **Similitud del Coseno** frente a 5 arquetipos comerciales (Alternativa aplicada al modelo Big Five) y cruza el resultado con métricas de *Engagement Rate* y *Ratio de Viralidad*.

---

## Estructura del Proyecto

Todos los reportes generados se almacenan automáticamente de forma organizada dentro del directorio `dataScrap/`:

```text
Tiktakscrap/
├── .venv/                                     # Entorno virtual aislado (Python 3.12 via uv)
├── dataScrap/                                 # Carpeta de salida de datos y reportes
│   ├── khaby.lame_datos.json                  # Datos jerárquicos (Perfil + 10 videos)
│   ├── khaby.lame_publicaciones.csv           # Tabla desnormalizada (UTF-8-SIG para Excel)
│   └── khaby.lame_analisis_hf.json            # Arquetipo IA + Métricas de Engagement
├── scraper_tiktok.py                          # Motor de extracción con Playwright
├── analizar_embeddings.py                     # Motor de Embeddings con Hugging Face
└── README.md                                  # Documentación del proyecto
```

---

## Guía de Instalación y Configuración (Comandos Base en PowerShell)

```powershell
# 1. Instalar uv en tu usuario (toma unos 5 segundos)
powershell -ExecutionPolicy ByPass -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

# 2. Actualizar la ruta de la consola actual para que reconozca el comando uv
$env:Path = "C:\Users\Fl0c\.local\bin;$env:Path"
# 3. Descargar Python 3.12 automáticamente y crear el entorno .venv en tu carpeta actual
uv venv .venv --python 3.12

# 4. Activar el entorno virtual del proyecto
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.\.venv\Scripts\Activate.ps1



# 5. Instalar Playwright dentro de ese .venv y descargar Chromium
uv pip install playwright
playwright install chromium

# Activar virtual enviroment
# To Activate the virtual enviroment with: .
venv\Scripts\activate (powershell)

# Ejecutar programa
python scraper_tiktok.py khabi.lame


# Embeddings
uv pip install sentence-transformers
New-Item -Path "analizar_embeddings.py" -ItemType File -Force
code analizar_embeddings.py
```

---

## Ejemplos de Ejecución y Salida

### 1. Extracción de Perfil y Publicaciones
```powershell
python scraper_tiktok.py khaby.lame
```
**Ejemplo de salida (`dataScrap/khaby.lame_datos.json`):**
```json
{
    "perfil": {
        "username": "khaby.lame",
        "nombre": "Khaby Lame",
        "biografia": "Se vuoi ridere sei nel posto giusto",
        "seguidores": 162800000,
        "total_publicaciones": 1215
    },
    "ultimas_publicaciones": [
        {
            "video_id": "7698770783367171359",
            "fecha_timestamp": 1792509783,
            "likes": 145200,
            "comentarios": 3410,
            "compartidos": 8920
        }
    ]
}
```

### 2. Análisis de Embeddings y Engagement
```powershell
python .\analizar_embeddings.py candido...fitnnes_datos.json
```
**Ejemplo de salida (`dataScrap/candido...fitnnes_analisis_hf.json`):**
```json
{
    "username": "candido...fitnnes",
    "arquetipo_dominante": "Estilo de Vida y Fitness",
    "scores_embeddings_hf": {
        "Estilo de Vida y Fitness": 0.4821,
        "Entretenimiento y Humor": 0.2104,
        "Comunidad y Tendencias": 0.1985,
        "Educación y Tecnología": 0.1542,
        "Negocios y Corporativo": 0.1120
    },
    "metricas_engagement": {
        "engagement_rate_porcentaje": 4.251,
        "ratio_viralidad_compartidos_vs_likes_porcentaje": 8.45
    }
}
```

---

## Conclusiones Analíticas y Propuesta de Valor (TikTok AI Scouting Engine)

1. **Detección de Audiencia Inactiva (Seguidores vs. Engagement):** El cruce de datos demuestra que cuentas masivas (ej. `@tiktok` con 96.4M de seguidores) pueden presentar un *Engagement Rate* de apenas **0.016%**, mientras que creadores de nicho superan el **4%**.
2. **Métrica de Viralidad Real (`compartidos / likes`):** Identifica qué publicaciones activan el motor de recomendación algorítmica más allá del *like* pasivo.
3. **Automatización de Brand-Fit con Embeddings:** Permite a agencias de marketing y marcas clasificar automáticamente el nicho comercial de un creador (Fitness, Tech, Humor, Corporativo) con costo **$0 en APIs externas**.