# Frontend - Streamlit Application

## Propósito

Frontend refactorizado que actúa como **cliente HTTP** del backend FastAPI. Su única responsabilidad es la **presentación y interacción con el usuario**.

## Arquitectura

```
frontend/
├── streamlit_app/
│   ├── app_refactored.py      # Aplicación principal refactorizada
│   ├── services/               # Servicios HTTP
│   │   ├── __init__.py
│   │   └── api_client.py      # Cliente HTTP al backend
│   ├── components/             # Componentes UI reutilizables (futuro)
│   └── pages/                  # Páginas adicionales (futuro)
├── requirements.txt
└── README.md
```

## Responsabilidades

✅ **UI/UX**: Interfaz de usuario con Streamlit
✅ **Validación de Entrada**: Validar datos antes de enviar al backend
✅ **Presentación**: Formatear y mostrar respuestas del backend
✅ **Estado de UI**: Gestionar estado de la sesión Streamlit
✅ **Navegación**: Gestionar flujo entre páginas

❌ **NO debe contener**: Lógica de negocio, acceso directo a BD, llamadas a OpenAI

## Separación Frontend/Backend

### ❌ ANTES (Monolítico)

```python
# Frontend accedía directamente a la BD
import psycopg2

conn = psycopg2.connect(...)
matches = conn.execute("SELECT * FROM matches")
```

### ✅ AHORA (Separado)

```python
# Frontend llama al backend via HTTP
from services.api_client import get_api_client

api = get_api_client()
matches = api.get_matches(source="postgres")
```

## API Client

### Uso Básico

```python
from services.api_client import get_api_client

# Obtener cliente
api = get_api_client()

# Health check
health = api.health_check()
print(health["status"])  # "healthy"

# Obtener competiciones
competitions = api.get_competitions(source="postgres")

# Obtener partidos
matches = api.get_matches(
    source="postgres",
    competition_name="UEFA Euro",
    limit=50
)

# Búsqueda semántica
result = api.search(
    match_id=3943043,
    query="¿Quién ganó el partido?",
    language="spanish",
    top_n=10
)

print(result["answer"])
```

### Configuración

El cliente se configura via variable de entorno:

```bash
# .env
BACKEND_URL=http://localhost:8000
```

O al crear el cliente:

```python
from services.api_client import APIClient

# URL específica
api = APIClient(base_url="http://backend:8000")
```

## Estructura de la Aplicación

### app_refactored.py

```python
import streamlit as st
from services.api_client import get_api_client

# Configuración de página
st.set_page_config(
    page_title="RAG Challenge",
    page_icon="⚽",
    layout="wide",
)

# Inicializar cliente API
api_client = get_api_client()

# Sidebar
with st.sidebar:
    source = st.selectbox("Database", ["postgres", "sqlserver"])
    mode = st.radio("Mode", ["user mode", "developer mode"])

# Contenido principal
try:
    # Obtener datos del backend
    matches = api_client.get_matches(source=source)

    # Mostrar UI
    selected_match = st.selectbox("Select match", matches)

    # Búsqueda
    if st.button("Search"):
        result = api_client.search(
            match_id=selected_match["match_id"],
            query=question,
            source=source
        )
        st.markdown(result["answer"])

except Exception as e:
    st.error(f"Backend error: {e}")
```

## Componentes UI (Futuro)

Crear componentes reutilizables en `components/`:

```python
# components/match_selector.py
import streamlit as st
from typing import List, Dict

def match_selector(matches: List[Dict]) -> Dict:
    """
    Componente para seleccionar un partido.

    Args:
        matches: Lista de partidos

    Returns:
        Partido seleccionado
    """
    options = [
        f"{m['home_team_name']} vs {m['away_team_name']}"
        for m in matches
    ]

    selected_index = st.selectbox(
        "Select a match:",
        range(len(options)),
        format_func=lambda i: options[i]
    )

    return matches[selected_index]
```

Uso:

```python
from components.match_selector import match_selector

matches = api.get_matches()
selected = match_selector(matches)
```

## Páginas Múltiples (Futuro)

Organizar en páginas:

```
pages/
├── 1_🏠_Home.py
├── 2_⚽_Matches.py
├── 3_📊_Statistics.py
└── 4_🔍_Search.py
```

Streamlit detecta automáticamente páginas en la carpeta `pages/`.

## Manejo de Errores

### Mostrar Errores del Backend

```python
try:
    result = api.search(...)
    st.success("Search completed!")
    st.markdown(result["answer"])

except requests.HTTPError as e:
    if e.response.status_code == 404:
        st.error("Match not found")
    elif e.response.status_code == 400:
        st.error("Invalid request parameters")
    else:
        st.error(f"Server error: {e}")

except requests.ConnectionError:
    st.error(f"Cannot connect to backend at {api.base_url}")
    st.info("Make sure the backend is running")

except Exception as e:
    st.error(f"Unexpected error: {e}")
    if mode == "developer mode":
        st.exception(e)
```

### Validación de Entrada

```python
question = st.text_area("Your question:")

if st.button("Search"):
    # Validar antes de enviar
    if not question.strip():
        st.error("Please enter a question")
        st.stop()

    if len(question) > 1000:
        st.warning("Question too long, will be truncated")
        question = question[:1000]

    # Enviar al backend
    result = api.search(query=question, ...)
```

## Estado y Caching

### Session State

```python
# Inicializar estado
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# Guardar búsqueda
st.session_state.search_history.append({
    "question": question,
    "answer": result["answer"],
    "timestamp": datetime.now()
})

# Mostrar historial
with st.expander("Search History"):
    for item in st.session_state.search_history:
        st.write(f"{item['timestamp']}: {item['question']}")
```

### Caching de Datos

```python
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_matches(source: str):
    """Cachear lista de partidos."""
    api = get_api_client()
    return api.get_matches(source=source)

# Uso
matches = load_matches(source)  # Se cachea automáticamente
```

## Modo Usuario vs Desarrollador

```python
mode = st.radio("Mode", ["user mode", "developer mode"])

if mode == "user mode":
    # UI simplificada
    st.text_area("Ask a question")

else:  # developer mode
    # UI con opciones avanzadas
    st.text_area("Ask a question")

    with st.expander("Advanced Options"):
        algorithm = st.selectbox("Algorithm", ["cosine", "l2", "inner_product"])
        model = st.selectbox("Model", ["ada-002", "t3-small", "t3-large"])
        top_n = st.slider("Top N", 1, 50, 10)

    # Mostrar metadata
    if result:
        with st.expander("Debug Info"):
            st.json(result["metadata"])
```

## Testing del Frontend

```python
import pytest
from services.api_client import APIClient
from unittest.mock import Mock, patch

def test_api_client():
    """Test del cliente API con mock."""
    with patch("services.api_client.requests.get") as mock_get:
        # Configure mock
        mock_get.return_value.json.return_value = {"status": "healthy"}

        # Test
        api = APIClient(base_url="http://test")
        health = api.health_check()

        assert health["status"] == "healthy"
        mock_get.assert_called_once()
```

## Deployment

### Local

```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app/app_refactored.py
```

### Docker (Futuro)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY streamlit_app/ ./streamlit_app/

ENV BACKEND_URL=http://backend:8000

CMD ["streamlit", "run", "streamlit_app/app_refactored.py", "--server.port=8501"]
```

## Variables de Entorno

```bash
# Backend URL
BACKEND_URL=http://localhost:8000

# Streamlit config (opcional)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

## Buenas Prácticas

1. **No Lógica de Negocio**: Solo UI y presentación
2. **Validación Básica**: Validar entrada antes de enviar
3. **Error Handling**: Mostrar errores de forma amigable
4. **Loading States**: Usar `st.spinner()` para operaciones lentas
5. **Caching**: Cachear datos que no cambian frecuentemente
6. **Responsive**: Usar `st.columns()` para layouts adaptativos
7. **Session State**: Gestionar estado de la sesión apropiadamente
8. **Modular**: Extraer componentes reutilizables

## Próximos Pasos

- [ ] Crear componentes UI reutilizables
- [ ] Agregar más páginas (estadísticas, comparaciones, etc.)
- [ ] Implementar autenticación (si se agrega al backend)
- [ ] Agregar visualizaciones con matplotlib/plotly
- [ ] Dockerizar frontend
- [ ] Agregar tests de UI
