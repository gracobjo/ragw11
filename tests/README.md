# Tests

## Ejecución

```bash
pip install pytest httpx
pytest tests/ -v
```

## Alcance

- `test_api.py`: Pruebas de endpoints de la API REST (health, sources, models, query, OpenAPI).
- Las pruebas usan `TestClient` de FastAPI; no requiere servidor en ejecución.
- Algunas pruebas pueden devolver 500 si no hay documentos indexados o el LLM no está disponible (se contempla en el procedimiento).
