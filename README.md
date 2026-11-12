# Proyecto Integrador DevOps — Backend Scoring Empresarial

Repositorio estructurado para demostrar e integrar prácticas **DevOps** sobre el backend de **Scoring Empresarial** (Django REST Framework + PostgreSQL + Machine Learning): **Contenedores, SonarCloud, Locust, CD con Rollback, IaC, Trazabilidad y Telemetría en Telegram**.

---

## ¿Qué se hizo y para qué sirve cada componente?

| Componente | Archivos principales | ¿Para qué sirve? |
|---|---|---|
| **Backend + ML** | `backend/`, `ml/` | API REST de scoring crediticio empresarial (`/api/v1/`) y modelos `.joblib` necesarios para inferencia y explicabilidad SHAP. |
| **Healthcheck** | `backend/config/views.py`, `backend/config/urls.py` | Expone `GET /api/v1/health/` verificando que Django y PostgreSQL respondan. Es la base para Docker y para decidir si un despliegue requiere *rollback*. |
| **Contenedores** | `docker/backend.Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml` | Empaqueta el backend de forma reproducible, ejecuta migraciones automáticamente al iniciar y levanta `PostgreSQL + Backend + Locust`. |
| **Pruebas de Rendimiento** | `tests/performance/locustfile.py`, `locust_smoke.py` | Simula usuarios concurrentes contra la API para medir latencia (p95), peticiones por segundo (RPS) y tasa de errores. |
| **Trazabilidad** | `docs/traceability_matrix.md` | Conecta cada requisito del proyecto integrador con su implementación, prueba automatizada y evidencia. |
| **CI + SonarCloud** | `.github/workflows/ci.yml`, `sonar-project.properties` | Ejecuta *linting* (`ruff`), pruebas unitarias con cobertura (`pytest --cov`) y deja listo el análisis estático de calidad en **SonarCloud**. |
| **CD con Rollback** | `scripts/deploy_with_rollback.sh`, `.github/workflows/cd-rollback.yml` | Despliega una nueva versión en contenedor, verifica su salud y, si falla, **revierte automáticamente** a la imagen anterior (`:previous`). |
| **IaC (Terraform)** | `infra/main.tf`, `infra/variables.tf`, `infra/outputs.tf` | Define de forma declarativa la red privada, el volumen persistente de BD y los contenedores, permitiendo recrear el entorno con un comando. |
| **Telemetría en Telegram** | `scripts/notify_telegram.py` | Envía notificaciones en tiempo real (éxito, fallo o rollback) a un chat/grupo de Telegram. Funciona en modo *dry-run* si aún no hay credenciales. |

---

## Estructura del repositorio

```text
prestamos_pruebas/
├── backend/                     # Código fuente del backend Django y pruebas
├── ml/                          # Features y artefactos (.joblib) para scoring
├── docker/
│   ├── backend.Dockerfile       # Imagen Python 3.12 + dependencias + HEALTHCHECK
│   └── entrypoint.sh            # Migraciones automáticas + arranque con Daphne
├── docker-compose.yml           # Orquestación local: db, backend y locust
├── tests/
│   └── performance/
│       ├── locustfile.py        # Escenarios completos (auth, perfil, evaluaciones, lookup)
│       ├── locust_smoke.py      # Smoke test rápido de salud post-despliegue
│       └── requirements.txt     # Dependencias aisladas para rendimiento
├── infra/                       # Infraestructura como Código (Terraform + Docker)
├── scripts/
│   ├── deploy_with_rollback.sh  # Lógica de despliegue simulado + rollback automático
│   └── notify_telegram.py       # Cliente ligero para Bot API de Telegram
├── .github/workflows/
│   ├── ci.yml                   # Pipeline CI (Ruff + Pytest/Coverage + SonarCloud + Telegram)
│   └── cd-rollback.yml          # Pipeline CD (Deploy + Locust Smoke + Rollback + Telegram)
├── docs/
│   └── traceability_matrix.md   # Matriz de trazabilidad requisitos ↔ pruebas
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
