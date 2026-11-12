# Proyecto Integrador DevOps — Backend Scoring Empresarial

Repositorio estructurado para demostrar e integrar prácticas **DevOps** sobre el backend de **Scoring Empresarial** (Django REST Framework + PostgreSQL + Machine Learning): **Contenedores, SonarCloud, Locust, CD con Rollback, IaC, Trazabilidad y Telemetría en Telegram**.

---

## ¿Qué se hizo y para qué sirve cada componente?

| Componente | Archivos principales | ¿Para qué sirve? |
|---|---|---|
| **Backend + ML** | `backend/`, `ml/` | API REST de scoring crediticio empresarial (`/api/v1/`) y modelos `.joblib` necesarios para inferencia y explicabilidad SHAP. |
| **Healthcheck** | `backend/config/views.py`, `backend/config/urls.py` | Expone `GET /api/v1/health/` verificando que Django y PostgreSQL respondan. Es la base para Docker y para decidir si un despliegue requiere *rollback*. |
| **Contenedores & QA** | `docker/backend.Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml` | Empaqueta el backend en `python:3.11-slim` y orquesta `db`, `localstack`, `backend`, `test` (runner QA inmutable que retorna Exit Code 0) y `locust`. |
| **Pruebas y Calidad (AAA + BVA)** | `backend/apps/*/tests/`, `backend/pytest.ini` | Pruebas unitarias estructuradas bajo el patrón AAA, BVA con `@pytest.mark.parametrize` y Quality Gate con `--cov-fail-under=80`. |
| **Pruebas de API y Contrato** | `backend/apps/scoring/tests/test_api_contracts.py` | Pruebas HTTP con `requests` y validación de contrato de respuestas con `jsonschema`. |
| **Pruebas de Rendimiento** | `tests/performance/locustfile.py`, `locust_smoke.py` | Simula usuarios concurrentes contra la API para medir latencia (p95), peticiones por segundo (RPS) y tasa de errores. |
| **Trazabilidad** | `docs/traceability_matrix.md` | Conecta cada semana y requisito del proyecto integrador con su implementación, prueba automatizada y evidencia. |
| **CI con Docker Compose** | `.github/workflows/ci.yml` | Ejecuta *linting* (`ruff`), levanta el entorno de pruebas con `docker compose run --rm test` y notifica a Telegram. |
| **Análisis Estático (SonarCloud)** | `.github/workflows/sonar.yml`, `sonar-project.properties` | Pipeline preventivo que detecta Code Smells, vulnerabilidades y deuda técnica antes de llegar a producción. |
| **CD con Rollback y Staging** | `scripts/deploy.py`, `.github/workflows/cd-rollback.yml` | Despliega primero en Staging con Smoke Tests de Locust, pasa a Producción y ejecuta **rollback automático** ante fallo (HTTP 500). |
| **IaC (LocalStack AWS + Terraform)**| `scripts/init_localstack.py`, `docker-compose.yml`, `infra/` | Emula AWS S3 (`prestamos-documentos-bucket`) y colas SQS con `boto3`, además de Terraform para recursos Docker. |
| **Telemetría en Telegram** | `scripts/notify_telegram.py` | Envía notificaciones en tiempo real (éxito, fallo o rollback) a un chat/grupo de Telegram. Funciona en modo *dry-run* si aún no hay credenciales. |

---

## Estructura del repositorio

```text
prestamos_pruebas/
├── backend/                     # Código fuente del backend Django y pruebas
│   ├── pytest.ini               # Configuración pytest con Quality Gate --cov-fail-under=80
│   ├── requirements.txt         # Dependencias (incluye jsonschema y boto3)
│   └── apps/                    # Apps de dominio con suites bajo patrón AAA y BVA
├── ml/                          # Features y artefactos (.joblib) para scoring
├── docker/
│   ├── backend.Dockerfile       # Imagen python:3.11-slim + dependencias + HEALTHCHECK
│   └── entrypoint.sh            # Migraciones automáticas + arranque con Daphne
├── docker-compose.yml           # Orquestación: db, localstack, backend, test (QA runner) y locust
├── tests/
│   └── performance/
│       ├── locustfile.py        # Escenarios de estrés (RPS y latencia)
│       ├── locust_smoke.py      # Smoke test rápido para Staging
│       └── requirements.txt     # Dependencias aisladas para rendimiento
├── infra/                       # Infraestructura como Código (Terraform + Docker)
├── scripts/
│   ├── init_localstack.py       # Aprovisionamiento IaC en LocalStack (S3 + SQS con boto3)
│   ├── deploy.py                # CD en Python con Staging, Prod y Rollback ante fallo (HTTP 500)
│   ├── deploy_with_rollback.sh  # Script shell alternativo de rollback
│   └── notify_telegram.py       # Telemetría móvil vía Bot API de Telegram
├── .github/workflows/
│   ├── ci.yml                   # Pipeline CI (Ruff + Docker Compose QA Tests + Telegram)
│   ├── sonar.yml                # Pipeline SonarCloud (Quality Gate, Code Smells, Vulnerabilidades)
│   └── cd-rollback.yml          # Pipeline CD (Staging Smoke + Prod Deploy + Rollback + Telegram)
├── docs/
│   └── traceability_matrix.md   # Matriz de trazabilidad integral (Semanas 1 a 10)
├── PRESENTACION_QA_DEVSECOPS.md # Diapositivas para exposición del proyecto (Semanas 1 a 10)
├── sonar-project.properties     # Configuración de SonarCloud
├── .env.example                 # Variables de entorno de ejemplo
└── .gitignore
```

---

## Cómo usar cada herramienta paso a paso

### 1. Contenedores (Docker Compose)
Levantar la base de datos PostgreSQL y el backend:
```bash
docker compose up -d --build
```

Verificar que el backend y la base de datos están arriba:
```bash
curl http://localhost:8000/api/v1/health/
```
Respuesta esperada (`HTTP 200`):
```json
{"status": "ok", "database": "up", "version": "dev"}
```

Ver logs o detener contenedores:
```bash
docker compose logs -f backend
docker compose down
```

---

### 2. Pruebas de rendimiento (Locust)

**Opción A — Con interfaz web (ideal para demostración visual):**
```bash
docker compose --profile perf up locust
```
Luego abre `http://localhost:8089`, configura usuarios y *spawn rate*, y observa las gráficas en vivo.

**Opción B — Modo headless (automatizado para CI/CD):**
```bash
pip install -r tests/performance/requirements.txt
locust -f tests/performance/locust_smoke.py \
  --headless --users 10 --spawn-rate 2 --run-time 30s \
  --host http://localhost:8000
```

---

### 3. CD con Rollback (despliegue simulado)
Ejecutar manualmente en Git Bash / Linux:
```bash
chmod +x scripts/deploy_with_rollback.sh
APP_VERSION=v1.0.0 ./scripts/deploy_with_rollback.sh
```
¿Qué hace internamente?
1. Guarda la imagen actual `prestamos-backend:latest` como `prestamos-backend:previous`.
2. Construye `prestamos-backend:<APP_VERSION>` y levanta el contenedor.
3. Consulta `/api/v1/health/` hasta 15 veces.
4. Si no responde `200 OK`, **revierte** `:latest` a `:previous`, reinicia el contenedor estable y envía alerta `ROLLBACK` a Telegram.

*(Para demostrar un fallo en GitHub Actions, ve a **Actions → CD - Simulated Deploy, Locust Smoke & Rollback → Run workflow** y selecciona `simulate_failure = true`.)*

> **Nota sobre Jenkins:** Si se requiere usar Jenkins en lugar de GitHub Actions, un `Jenkinsfile` solo necesita invocar `./scripts/deploy_with_rollback.sh` y `python scripts/notify_telegram.py` en sus *stages*.

---

### 4. IaC con Terraform (`infra/`)
```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```
Para destruir la infraestructura creada por Terraform:
```bash
terraform destroy -auto-approve
```

---

### 5. Integración posterior (SonarCloud y Telegram)

#### Conectar SonarCloud
1. Inicia sesión en [SonarCloud](https://sonarcloud.io/) e importa el repositorio `DMaTeoG/prestamos_pruebas`.
2. Copia el `projectKey` y `organization` en `sonar-project.properties`.
3. En GitHub, ve a **Settings → Secrets and variables → Actions** y agrega el secreto `SONAR_TOKEN`.
4. En el siguiente `push`, `.github/workflows/ci.yml` enviará automáticamente el análisis y la cobertura (`coverage.xml`).

#### Conectar Telemetría en Telegram
1. Crea un bot en Telegram hablando con `@BotFather` (`/newbot`) y guarda el `TELEGRAM_BOT_TOKEN`.
2. Obtén tu `TELEGRAM_CHAT_ID` (por ejemplo, escribiendo al bot y consultando `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. Agrega ambos valores como Secrets en GitHub Actions (`TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`), o expórtalos localmente en tu terminal.
4. Prueba el envío:
   ```bash
   python scripts/notify_telegram.py --title "Prueba" --status "SUCCESS" --details "Bot conectado"
   ```
