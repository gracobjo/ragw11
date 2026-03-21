"""
Pruebas de la API REST.
Ejecutar: pytest tests/test_api.py -v
"""
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health():
    """El endpoint /health debe responder 200."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_sources():
    """El endpoint /api/sources debe devolver una lista (puede estar vacía)."""
    r = client.get("/api/sources")
    assert r.status_code == 200
    data = r.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_get_models():
    """El endpoint /api/models debe responder (lista o mensaje)."""
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data


def test_query_empty_fails():
    """Query sin pregunta debe fallar por validación."""
    r = client.post("/api/query", json={})
    assert r.status_code == 422  # Validation error


def test_query_with_question():
    """Query con pregunta debe responder (puede fallar si no hay docs indexados)."""
    r = client.post("/api/query", json={"pregunta": "¿Qué hay en los documentos?"})
    # 200 si hay docs, 500 si no hay índice o falla el LLM
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        data = r.json()
        assert "answer" in data
        assert "sources" in data


def test_openapi_schema():
    """OpenAPI schema debe estar disponible."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data
    assert "paths" in data
