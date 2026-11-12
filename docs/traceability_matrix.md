# Matriz de Trazabilidad — Proyecto Integrador DevOps (Backend)

| ID | Requisito / Entregable | Implementación en el repositorio | Verificación automatizada | Evidencia / Resultado |
|---|---|---|---|---|
| **DEV-01** | **Contenedores** (Backend + BD + Locust) | `docker/backend.Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml` | `docker compose up -d --build` + `HEALTHCHECK` en `/api/v1/health/` | Contenedores en estado `healthy` |
| **DEV-02** | **SonarCloud** (Calidad y cobertura) | `sonar-project.properties`, `.github/workflows/ci.yml` | `ruff check`, `pytest --cov --cov-report=xml`, `sonarqube-scan-action` | Quality Gate + `coverage.xml` |
| **DEV-03** | **Locust** (Pruebas de rendimiento) | `tests/performance/locustfile.py`, `tests/performance/locust_smoke.py` | Ejecución headless (`--users 10 --spawn-rate 2 --run-time 30s`) | Reporte HTML/CSV de latencia p95 y % errores |
| **DEV-04** | **CD con Rollback** (Despliegue simulado) | `scripts/deploy_with_rollback.sh`, `.github/workflows/cd-rollback.yml` | Healthcheck post-despliegue + smoke test Locust; si falla → rollback a `:previous` | Log de despliegue / rollback automático |
| **DEV-05** | **IaC** (Infraestructura como Código) | `infra/main.tf`, `infra/variables.tf`, `infra/outputs.tf` | `terraform init`, `terraform validate`, `terraform plan` / `apply` | Red, volumen y contenedores declarativos |
| **DEV-06** | **Telemetría en Telegram** | `scripts/notify_telegram.py` (invocado desde CI/CD y rollback) | Envío vía Bot API de Telegram (modo *dry-run* si faltan credenciales) | Mensaje con estado, versión y métricas |
| **TRZ-01** | **Trazabilidad de Auditoría y API** | `backend/apps/audit/`, `backend/apps/scoring/`, `backend/config/views.py` | `pytest` en `backend/apps/*/tests/` | Registro en `AuditLog` y `Evaluation` |
