# Adapters Layer

## Propósito

La capa de **adapters** proporciona **integraciones con servicios externos**. Encapsula las llamadas a APIs de terceros, servicios cloud, y otros sistemas externos, permitiendo que el resto de la aplicación trabaje con interfaces simples sin conocer detalles de implementación.

## Responsabilidades

✅ **Integración Externa**: Comunicarse con APIs de terceros (OpenAI, Azure, etc.)
✅ **Transformación de Datos**: Convertir entre formatos externos e internos
✅ **Manejo de Errores**: Capturar y traducir errores externos a excepciones de dominio
✅ **Retry Logic**: Implementar reintentos y circuit breakers
✅ **Autenticación**: Gestionar tokens, API keys, y credenciales

❌ **NO debe contener**: Lógica de negocio, acceso a BD, detalles de HTTP endpoints internos

## Estructura

```
adapters/
├── __init__.py
├── openai_client.py       # Adapter para OpenAI/Azure OpenAI
├── storage_client.py      # Adapter para almacenamiento (futuro)
└── README.md
```

## Patrón Adapter

### Principio

El patrón Adapter **traduce una interfaz externa a una interfaz que nuestra aplicación entiende**.

```
[Nuestra App] → [Adapter] → [Servicio Externo]
```

### Ejemplo: OpenAI Adapter

```python
import logging
from typing import List, Optional
from openai import AzureOpenAI

from app.core.config import get_settings
from app.domain.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIAdapter:
    """
    Adapter para OpenAI/Azure OpenAI API.

    Encapsula toda la lógica de comunicación con OpenAI,
    permitiendo que el resto de la app no conozca detalles de la API.
    """

    def __init__(self):
        """Inicializar cliente con configuración."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.openai.endpoint,
            api_key=settings.openai.api_key,
            api_version="2024-02-01",
        )

    def create_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """
        Generar embedding para un texto.

        Args:
            text: Texto a convertir en embedding
            model: Modelo de embedding a usar

        Returns:
            Vector de embeddings (lista de floats)

        Raises:
            EmbeddingGenerationError: Si falla la generación
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            # Traducir error externo a excepción de dominio
            raise EmbeddingGenerationError(
                f"Failed to create embedding: {e}"
            )

    def create_chat_completion(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 5000,
    ) -> str:
        """
        Generar respuesta de chat con el LLM.

        Args:
            messages: Lista de mensajes [{role, content}]
            model: Modelo a usar (por defecto del config)
            temperature: Temperatura de sampling (0-2)
            max_tokens: Tokens máximos en respuesta

        Returns:
            Texto generado por el LLM

        Raises:
            Exception: Si falla la generación
        """
        if model is None:
            model = settings.openai.model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to create chat completion: {e}")
            raise
```

## Convenciones

### 1. Interfaz Simple

El adapter debe exponer una interfaz **simple y orientada al negocio**:

**✅ BUENO**:
```python
def create_embedding(self, text: str, model: str) -> List[float]:
    """Interfaz simple."""
    ...
```

**❌ MALO**:
```python
def call_openai_embeddings_api_v2_with_retry(
    self, text: str, model: str, headers: dict, timeout: int
) -> OpenAIEmbeddingResponse:
    """Interfaz compleja que expone detalles de implementación."""
    ...
```

### 2. Ocultar Detalles de la API Externa

El código que usa el adapter **no debe saber** que está usando OpenAI:

```python
# Servicio que usa el adapter
def generate_summary(self, text: str) -> str:
    # No sabe que internamente usa OpenAI
    embedding = self.llm_adapter.create_embedding(text)
    ...
```

### 3. Traducir Errores

Convertir excepciones externas en excepciones de dominio:

```python
try:
    response = external_api.call()
except ExternalAPIError as e:
    # Traducir a excepción de dominio
    raise DomainSpecificError(f"Operation failed: {e}")
```

### 4. Logging

Registrar todas las llamadas externas:

```python
def create_embedding(self, text: str) -> List[float]:
    logger.info(f"Creating embedding for text of length {len(text)}")

    try:
        result = self.client.embeddings.create(...)
        logger.info("Embedding created successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to create embedding: {e}")
        raise
```

## Patrones Comunes

### Retry Logic

Implementar reintentos para APIs inestables:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class APIAdapter:

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def call_api(self, data: dict) -> dict:
        """Llamar API con reintentos automáticos."""
        return self.client.post("/endpoint", json=data)
```

### Circuit Breaker

Prevenir llamadas repetidas a servicios caídos:

```python
from circuitbreaker import circuit

class APIAdapter:

    @circuit(failure_threshold=5, recovery_timeout=60)
    def call_unstable_service(self) -> dict:
        """
        Circuit breaker abre después de 5 fallos
        y se recupera después de 60 segundos.
        """
        return self.client.get("/unstable")
```

### Caching

Cachear respuestas de APIs costosas:

```python
from functools import lru_cache

class OpenAIAdapter:

    @lru_cache(maxsize=1000)
    def create_embedding(self, text: str, model: str) -> List[float]:
        """Cachear embeddings ya generados."""
        return self.client.embeddings.create(...)
```

### Rate Limiting

Limitar velocidad de llamadas:

```python
from ratelimit import limits, sleep_and_retry

class APIAdapter:

    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 llamadas por minuto
    def call_rate_limited_api(self) -> dict:
        """Respetar límites de la API."""
        return self.client.get("/resource")
```

### Timeout

Establecer timeouts para llamadas:

```python
import requests

class HTTPAdapter:

    def call_with_timeout(self, url: str) -> dict:
        """Llamar con timeout de 30 segundos."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            raise TimeoutError("API call timed out")
```

## Dependency Injection

Hacer el adapter inyectable:

```python
# En dependencies.py
def get_openai_adapter() -> OpenAIAdapter:
    """Factory para crear adapter de OpenAI."""
    return OpenAIAdapter()

# En service
class SearchService:
    def __init__(
        self,
        openai_adapter: OpenAIAdapter,
    ):
        self.openai = openai_adapter

# En endpoint
@router.post("/search")
async def search(
    openai: OpenAIAdapter = Depends(get_openai_adapter)
):
    ...
```

## Testing

### Mock del Adapter

```python
from unittest.mock import Mock
import pytest

def test_service_with_mocked_adapter():
    # Arrange
    mock_adapter = Mock(spec=OpenAIAdapter)
    mock_adapter.create_embedding.return_value = [0.1, 0.2, 0.3]

    service = SearchService(openai_adapter=mock_adapter)

    # Act
    result = service.search("test query")

    # Assert
    mock_adapter.create_embedding.assert_called_once_with("test query")
    assert result is not None
```

### Integration Tests

Testear contra API real (con cuidado):

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_KEY"), reason="No API key")
def test_real_openai_call():
    """Test de integración con OpenAI real."""
    adapter = OpenAIAdapter()

    embedding = adapter.create_embedding("Hello world")

    assert len(embedding) == 1536  # ada-002 dimension
    assert all(isinstance(x, float) for x in embedding)
```

## Ejemplos de Adapters

### Storage Adapter

```python
class StorageAdapter:
    """Adapter para almacenamiento en cloud."""

    def __init__(self):
        self.client = BlobServiceClient(...)

    def upload_file(self, file_path: str, blob_name: str) -> str:
        """Subir archivo y retornar URL."""
        with open(file_path, "rb") as data:
            blob_client = self.client.get_blob_client(blob_name)
            blob_client.upload_blob(data)
        return blob_client.url

    def download_file(self, blob_name: str, dest_path: str) -> None:
        """Descargar archivo."""
        blob_client = self.client.get_blob_client(blob_name)
        with open(dest_path, "wb") as file:
            file.write(blob_client.download_blob().readall())
```

### Email Adapter

```python
class EmailAdapter:
    """Adapter para envío de emails."""

    def __init__(self):
        self.client = SendGridAPIClient(api_key=settings.sendgrid_key)

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> bool:
        """Enviar email."""
        try:
            message = Mail(
                from_email="noreply@app.com",
                to_emails=to,
                subject=subject,
                html_content=body,
            )
            response = self.client.send(message)
            return response.status_code == 202

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise EmailSendError(f"Failed to send email: {e}")
```

## Buenas Prácticas

1. **Interfaz Simple**: Ocultar complejidad de la API externa
2. **Error Handling**: Traducir errores externos a excepciones de dominio
3. **Logging**: Registrar todas las llamadas y errores
4. **Retry Logic**: Implementar reintentos para APIs inestables
5. **Timeouts**: Siempre establecer timeouts
6. **Caching**: Cachear cuando tenga sentido
7. **Testing**: Facilitar mocking para tests unitarios
8. **Configuration**: Usar settings centralizados, no hardcodear URLs/keys
9. **Monitoring**: Agregar métricas de llamadas, latencia, errores

## Anti-Patrones

❌ **Exponer tipos externos**:
```python
# MALO - expone OpenAIEmbeddingResponse
def create_embedding(self) -> OpenAIEmbeddingResponse:
    ...
```

❌ **Lógica de negocio en adapter**:
```python
# MALO - validación de negocio en adapter
def create_embedding(self, text: str):
    if len(text) < 10:  # Regla de negocio
        raise ValueError("Text too short")
    ...
```

❌ **Hardcodear configuración**:
```python
# MALO - hardcoded
def __init__(self):
    self.api_key = "sk-xxx"  # ¡Nunca hacer esto!
```

✅ **Usar configuración centralizada**:
```python
# BIEN
def __init__(self):
    self.api_key = settings.openai.api_key
```
