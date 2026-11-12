# Contexto Completo y Guía del Proyecto — `prestamos_pruebas`

Este documento detalla la estructura completa del repositorio, la ubicación de cada componente, su propósito técnico en el semillero DevOps y cómo se conectan para cumplir con el **Proyecto Integrador (Semanas 11 y 12)**.

---

## 1. Mapa General del Repositorio

El repositorio está clonado localmente en:
`C:\Users\Admin\Desktop\compilador\prestamos_pruebas`

Y sincronizado en GitHub:
`https://github.com/DMaTeoG/prestamos_pruebas`

```text
prestamos_pruebas/
├── backend/                       # 1. API Core y Pruebas Unitarias
│   ├── apps/                      #    Módulos de negocio (cuentas, scoring, auditoría, etc.)
│   ├── config/                    #    Configuración Django y Healthcheck (/api/v1/health/)
│   └── pyproject.toml             #    Reglas de linting y calidad con Ruff
├── ml/                            # 2. Machine Learning y Artefactos
│   ├── src/                       #    Features e inferencia del modelo de riesgo
│   └── artifacts/                 #    Modelos serializados (.joblib)
├── docker/                        # 3. Contenedores y Empaquetado
│   ├── backend.Dockerfile         #    Imagen de producción/QA con Healthcheck nativo
│   └── entrypoint.sh              #    Automatización de migraciones y arranque Daphne
├── docker-compose.yml             #    Orquestación local: PostgreSQL + Backend + Locust
├── tests/                         # 4. Pruebas de Rendimiento y Smoke Tests
│   └── performance/
│       ├── locustfile.py          #    Carga contra endpoints protegidos y de negocio
│       └── locust_smoke.py        #    Smoke test ultraligero para validación en CD
├── infra/                         # 5. Infraestructura como Código (IaC con Terraform)
│   ├── main.tf                    #    Declaración de red, volumen y contenedores Docker
│   ├── variables.tf               #    Parámetros configurables (puertos, credenciales)
│   └── outputs.tf                 #    URLs y nombres exportados tras el despliegue
├── scripts/                       # 6. Automatización de Despliegue y Telemetría
│   ├── deploy_with_rollback.sh    #    Lógica de despliegue con reversión automática
│   ├── deploy.py                  #    Alternativa de despliegue controlado en Python
│   └── notify_telegram.py         #    Cliente HTTP para alertas en tiempo real al Bot
├── .github/workflows/             # 7. Pipelines de CI/CD (GitHub Actions)
│   ├── ci.yml                     #    Pipeline de calidad: Ruff + Pytest + Telegram
│   ├── cd-rollback.yml            #    Pipeline de entrega continua con prueba de rollback
│   └── sonar.yml                  #    Pipeline de escaneo y reporte a SonarCloud
├── docs/                          # 8. Documentación y Trazabilidad
│   ├── traceability_matrix.md     #    Matriz que mapea requisitos ↔ código ↔ pruebas
│   └── contexto_completo.md       #    Este documento
├── sonar-project.properties       # 9. Configuración de análisis estático SonarCloud
└── README.md                      # 10. Manual de ejecución rápida y comandos
```

---

## 2. Detalle de Cada Componente: ¿Dónde está y para qué sirve?

### A. Backend y Healthcheck (`backend/`)
- **[views.py](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/backend/config/views.py)** y **[urls.py](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/backend/config/urls.py)**:
  - **Ubicación:** `backend/config/views.py` (función `health_check`)
  - **Para qué sirve:** Expone el endpoint `GET /api/v1/health/`. Verifica en tiempo real si el servidor web responde y si la conexión a la base de datos PostgreSQL está activa.
  - **Por qué es clave:** Es la sonda que usan Docker y el script de CD para saber si la aplicación arrancó bien o si debe abortar y hacer rollback.
- **[pyproject.toml](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/backend/pyproject.toml)**:
  - **Para qué sirve:** Define las reglas del linter `ruff` (orden de imports, largo de línea, exclusión de migraciones) para asegurar código limpio en cada commit.

---

### B. Machine Learning (`ml/`)
- **Ubicación:** `ml/src/` y `ml/artifacts/`
- **Para qué sirve:** Contiene el código de features y los artefactos `.joblib` que calculan el score empresarial (0 a 1000) y las explicaciones SHAP dentro del backend sin dependencias externas.

---

### C. Contenedores y Orquestación (`docker/` y `docker-compose.yml`)
- **[backend.Dockerfile](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/docker/backend.Dockerfile)**:
  - **Para qué sirve:** Construye una imagen liviana basada en `python:3.12-slim`, instala librerías de sistema (`libpq-dev`), copia el backend y define una directiva `HEALTHCHECK` nativa de Docker.
- **[entrypoint.sh](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/docker/entrypoint.sh)**:
  - **Para qué sirve:** Se ejecuta antes de levantar el servidor. Corre `python manage.py migrate --noinput` para que la base de datos siempre esté al día antes de aceptar peticiones.
- **[docker-compose.yml](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/docker-compose.yml)**:
  - **Para qué sirve:** Con un solo comando (`docker compose up -d`) levanta:
    1. **`db`**: PostgreSQL 16 con volumen persistente (`postgres_data`).
    2. **`backend`**: La API Django en el puerto `8000`, esperando a que la BD esté saludable (`condition: service_healthy`).
    3. **`locust`**: Herramienta de pruebas de carga con interfaz web en el puerto `8089` (perfil `perf`).

---

### D. Pruebas de Rendimiento (`tests/performance/`)
- **[locustfile.py](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/tests/performance/locustfile.py)**:
  - **Para qué sirve:** Simula el comportamiento real de analistas bancarios: inicia sesión con JWT, consulta perfil (`/api/v1/auth/me/`), lista evaluaciones de crédito (`/api/v1/evaluations/`) y busca empresas por NIT (`/api/v1/companies/lookup/`).
- **[locust_smoke.py](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/tests/performance/locust_smoke.py)**:
  - **Para qué sirve:** Prueba rápida (smoke test) de alta concurrencia al endpoint de salud para validar latencia mínima y estabilidad tras un despliegue en CD.

---

### E. CD con Rollback Automático (`scripts/` y `.github/workflows/cd-rollback.yml`)
- **[deploy_with_rollback.sh](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/scripts/deploy_with_rollback.sh)**:
  - **Para qué sirve:** Es el corazón del despliegue continuo con tolerancia a fallos:
    1. **Respaldo:** Toma la imagen actual `prestamos-backend:latest` y la etiqueta como `prestamos-backend:previous`.
    2. **Construcción y Despliegue:** Construye la nueva versión y recrea el contenedor backend.
    3. **Verificación de Salud:** Consulta `/api/v1/health/` hasta 15 veces consecutivas.
    4. **Rollback Automático:** Si el healthcheck falla, inmediatamente vuelve a levantar la versión `:previous`, restaura el servicio sin caída prolongada y notifica a Telegram con estado `ROLLBACK`.
- **[.github/workflows/cd-rollback.yml](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/.github/workflows/cd-rollback.yml)**:
  - **Para qué sirve:** Ejecuta el despliegue en GitHub Actions y permite seleccionar el parámetro manual `simulate_failure: true` para demostrar el rollback en vivo frente al evaluador.

---

### F. Infraestructura como Código — IaC (`infra/`)
- **[main.tf](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/infra/main.tf)**, **[variables.tf](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/infra/variables.tf)**, **[outputs.tf](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/infra/outputs.tf)**:
  - **Para qué sirve:** Usa **Terraform** con el proveedor de Docker para declarar de forma reproducible:
    - La red privada virtual de los contenedores (`prestamos_network_dev`).
    - El volumen persistente de PostgreSQL (`prestamos_pg_data_dev`).
    - Los contenedores de BD y Backend con sus respectivas variables de entorno y puertos.

---

### G. Telemetría en Telegram (`scripts/notify_telegram.py`)
- **[notify_telegram.py](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/scripts/notify_telegram.py)**:
  - **Para qué sirve:** Script en Python sin dependencias pesadas (usa `urllib`) que envía mensajes estructurados a tu Bot de Telegram (`@PrestamosDevOps_bot`):
    - Reporta inicio/éxito de pruebas unitarias (CI).
    - Reporta resultado del análisis de SonarCloud.
    - Notifica despliegues exitosos o rollbacks automáticos.
  - **Resiliencia:** Si faltan variables de entorno, corre en modo `dry-run` sin romper ningún pipeline.

---

### H. Calidad y SonarCloud (`sonar-project.properties` y `.github/workflows/sonar.yml`)
- **[sonar-project.properties](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/sonar-project.properties)**:
  - **Para qué sirve:** Define la clave del proyecto (`DMaTeoG_prestamos_pruebas`), la organización en SonarCloud (`dmateog`), rutas de código (`backend`), rutas de pruebas y exclusiones.
- **[.github/workflows/sonar.yml](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/.github/workflows/sonar.yml)**:
  - **Para qué sirve:** Corre en cada push, ejecuta `pytest --cov` para generar `backend/coverage.xml`, dispara el escáner de SonarCloud y notifica a Telegram.
  - **Estado actual:** **Quality Gate: PASSED**.

---

### I. Matriz de Trazabilidad (`docs/traceability_matrix.md`)
- **[traceability_matrix.md](file:///C:/Users/Admin/Desktop/compilador/prestamos_pruebas/docs/traceability_matrix.md)**:
  - **Para qué sirve:** Es el documento formal de auditoría para la entrega académica. Mapea cada uno de los 6 requisitos (Contenedores, Sonar, Locust, CD Rollback, IaC, Telegram) con sus archivos fuente, cómo se prueban y qué evidencia generan.

---

## 3. Resumen Rápido para Sustentar (Chuleta para Exponer)

1. **"¿Cómo aseguraron la calidad del código?"**
   > *"Usamos un linter estricto (`ruff`) y SonarCloud conectado vía GitHub Actions. Nuestro Quality Gate en SonarCloud está en estado **PASSED** sin bugs, vulnerabilidades ni duplicaciones en el código nuevo."*

2. **"¿Cómo garantizan que un despliegue defectuoso no tumbe el servicio?"**
   > *"Implementamos CD con Rollback en `scripts/deploy_with_rollback.sh`. Antes de actualizar, se respalda la imagen anterior. Tras levantar la nueva versión, el pipeline consulta la sonda `/api/v1/health/`. Si la nueva versión no responde, el sistema restaura automáticamente la imagen previa y manda una alerta `ROLLBACK` a Telegram."*

3. **"¿Cómo evaluaron el rendimiento?"**
   > *"Diseñamos escenarios con **Locust** en `tests/performance/locustfile.py`, midiendo autenticación JWT, búsqueda de NITs y evaluaciones de crédito, evaluando latencia p95 y estabilidad de conexiones."*

4. **"¿Cómo provisionan la infraestructura?"**
   > *"Mediante IaC con **Terraform** en la carpeta `infra/`. Redes, volúmenes persistentes y contenedores están declarados en código para ser recreados en cualquier ambiente con `terraform apply`."*
