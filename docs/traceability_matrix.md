# Matriz de Trazabilidad — QA & DevSecOps (10 Semanas)

| Semana | Requisito / Entregable | Implementación en el repositorio | Verificación automatizada | Evidencia / Resultado |
|:---:|---|---|---|---|
| **Semana 1** | **Pruebas Unitarias y Patrón AAA** | `backend/apps/*/tests/` (`test_validators.py`, `test_ratios.py`, `test_auth.py`, `test_scoring.py`) | `pytest` | Estructuración explícita bajo `# Arrange`, `# Act`, `# Assert`. |
| **Semana 2** | **Valores Límite (BVA) y Parametrización** | `test_validators.py`, `test_ratios.py`, `test_scoring.py`, `test_sources.py` | `@pytest.mark.parametrize`, `pytest.raises` | Pruebas DRY con fronteras de datos válidas e inválidas. |
| **Semana 3** | **Cobertura de Código y Quality Gate** | `backend/pytest.ini`, `backend/requirements.txt` | `pytest --cov=apps --cov-fail-under=80` | Umbral mínimo del 80% exigido formalmente en `pytest.ini`. |
| **Semana 4** | **Contenerización de Pruebas** | `docker/backend.Dockerfile` (`python:3.11-slim`), `docker-compose.yml` (servicio `test`) | `docker compose run --rm test` | Ejecución inmutable y aislada con retorno de `Exit Code 0`. |
| **Semana 5** | **Pruebas de API y JSON Schema** | `backend/apps/scoring/tests/test_api_contracts.py` | `requests`, `jsonschema.validate` | Verificación de códigos HTTP (200, 401, 404) y esquemas JSON. |
| **Semana 6** | **Integración Continua (CI)** | `.github/workflows/ci.yml` | GitHub Actions + `docker compose run --rm test` | Ejecución automatizada en cada `push` o `pull_request`. |
| **Semana 7** | **Análisis Estático (SonarCloud)** | `.github/workflows/sonar.yml`, `sonar-project.properties` | `ruff check`, `SonarSource/sonarqube-scan-action@v4` | Detección preventiva de Code Smells, vulnerabilidades y deuda. |
| **Semana 8** | **Carga y Rendimiento (Locust)** | `tests/performance/locustfile.py`, `tests/performance/locust_smoke.py`, `docker-compose.yml` | `locust --headless --users 10 --spawn-rate 2` | Reportes de Latencia (p95) y Requests Per Second (RPS). |
| **Semana 9** | **Despliegue Continuo (CD) y Rollback** | `scripts/deploy.py`, `.github/workflows/cd-rollback.yml`, `scripts/notify_telegram.py` | Smoke tests en Staging + Rollback ante HTTP 500 + Bot Telegram | CD auditable con rollback automático y alertas móviles. |
| **Semana 10**| **Infraestructura como Código (IaC)** | `docker-compose.yml` (`localstack`), `scripts/init_localstack.py`, `test_localstack_aws.py` | `boto3` creando S3 (`prestamos-documentos-bucket`) y SQS | Aprovisionamiento declarativo local de servicios AWS cloud. |
