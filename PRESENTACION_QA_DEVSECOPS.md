# Presentación Ejecutiva y Técnica: QA & DevSecOps (Semanas 1 a 10)
## Proyecto: Backend Scoring Empresarial (`prestamos_pruebas`)

> **Formato de Exposición:** Estilo diapositivas modulares divididas por separadores horizontales (`---`).  
> **Estructura Pedagógica:** Cada ruta de archivo incluye **su fragmento de código real**, explicación técnica y **Guion para el Expositor (Speaker Notes)**.  
> **Compatibilidad:** Visores Markdown (Marp, Obsidian Slides, VS Code Slide Show o lectura directa en pantalla).

---

<!-- slide -->
# 🖥️ Diapositiva 1: Portada y Resumen de la Auditoría

## Transformación Integral de Calidad, Automatización e Infraestructura
### De una auditoría inicial con fallas al 100% de cumplimiento estricto

* **Expositor / Rol:** Ingeniero Senior en QA (Quality Assurance) y DevSecOps
* **Proyecto Auditado:** API REST de Scoring Crediticio Empresarial (Python / Django REST / PostgreSQL / Machine Learning)
* **Objetivo:** Auditar, refactorizar e implementar de forma estricta las 10 semanas de prácticas de pruebas de software, calidad continua, contenerización inmutable, contratos de API, pipelines de CI/CD con rollback automático e Infraestructura como Código (IaC).

```text
================================================================================
📊 ESTADO INICIAL DE AUDITORÍA:  56.5% de cumplimiento (Gaps críticos detectados)
🏆 ESTADO TRAS REMEDIACIÓN:     100.0% de cumplimiento estricto (10/10 Semanas)
================================================================================
```

> 🎤 **Guion del Expositor:**  
> *"Buenos días. En esta sesión presentaremos la auditoría y evolución técnica de nuestro sistema de Scoring Empresarial. Al inicio de la auditoría encontramos que el proyecto cumplía parcialmente con las pruebas y carecía de validación de contratos, Quality Gates forzados y emulación cloud local. A continuación mostraremos exactamente qué se implementó, en qué archivos y con qué fragmentos de código logramos el 100% de cumplimiento de los estándares exigidos."*

---

<!-- slide -->
# 🗺️ Diapositiva 2: Mapa de Arquitectura DevSecOps de Extremo a Extremo

```mermaid
flowchart LR
    A["Desarrollo\nPython 3.11"] --> B["Pruebas Unitarias\nAAA + BVA + DRY"]
    B --> C["Quality Gate\npytest-cov >= 80%"]
    C --> D["Contenedor QA\nDocker Compose"]
    D --> E["CI Pipeline\nGitHub Actions"]
    E --> F["Análisis Estático\nSonarCloud + Ruff"]
    F --> G["Staging & Smoke\nLocust (RPS/Latencia)"]
    G --> H{"Healthcheck\nHTTP 200?"}
    H -- "Sí" --> I["Producción OK\nNotificación Telegram"]
    H -- "Fallo HTTP 500" --> J["Rollback Automático\nImagen :previous"]
    J --> K["Alerta Móvil\nTelegram Bot"]
    D -.-> L["IaC LocalStack\nAWS S3 + SQS (boto3)"]
```

### Principios Fundamentales Implementados
1. **Shift-Left Quality:** Pruebas tempranas AAA, BVA y bloqueo automático por debajo del 80% de cobertura.
2. **Inmutabilidad y Paridad:** Pruebas ejecutadas en contenedor `python:3.11-slim` idéntico a producción.
3. **Resiliencia Operativa:** Despliegue con verificación de Staging, rollback ante errores 500 y alertas push a Telegram.
4. **IaC Aislada:** Emulación local de AWS S3 y SQS con LocalStack y Boto3 (cero costos en la nube).

> 🎤 **Guion del Expositor:**  
> *"Nuestra arquitectura une todas las etapas: desde que el código se escribe con pruebas unitarias estructuradas, pasando por compuertas de cobertura y análisis estático en SonarCloud, hasta el despliegue continuo con reversión automática si la salud del sistema falla."*

---

<!-- slide -->
# 🧪 Diapositiva 3: Semana 1 — Pruebas Unitarias y Patrón AAA (Arrange, Act, Assert)

### El Requisito
* Utilizar Python con el framework **pytest**.
* Estructurar todas las pruebas unitarias basándose **estrictamente** en el patrón **AAA (Arrange, Act, Assert)**.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [test_validators.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/companies/tests/test_validators.py#L22-L34)
```python
def test_calculate_verification_digit_parametrized(nit_base: str, expected_dv: str):
    """Prueba unitaria bajo el patrón estricto AAA."""
    # Arrange: Preparación explícita del escenario y datos de prueba
    input_nit = nit_base

    # Act: Ejecución de la unidad de código bajo prueba
    calculated_dv = calculate_verification_digit(input_nit)

    # Assert: Verificación rigurosa del resultado obtenido vs esperado
    assert calculated_dv == expected_dv
```

#### 📍 Ruta 2: [test_ratios.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/financials/tests/test_ratios.py#L42-L73)
```python
    def test_complete_ratios_calculation_aaa(self):
        # Arrange: Construcción de estados financieros actual y previo
        stmt = FinancialStatement.objects.create(
            company=self.company, fiscal_year=2023,
            revenue=Decimal("1000000000.00"), current_assets=Decimal("400000000.00"),
            current_liabilities=Decimal("200000000.00"), total_assets=Decimal("800000000.00"),
            total_liabilities=Decimal("300000000.00"), financial_expenses=Decimal("50000000.00"),
            operating_income=Decimal("300000000.00"), net_income=Decimal("200000000.00")
        )
        prev_stmt = FinancialStatement.objects.create(company=self.company, fiscal_year=2022, revenue=Decimal("800000000.00"))

        # Act: Ejecución del motor de ratios financieros
        ratios = calculate_financial_ratios(stmt, prev_stmt)

        # Assert: Verificación de cada indicador financiero
        assert ratios["current_ratio"] == 2.0         # Liquidez: 400M / 200M
        assert ratios["debt_ratio"] == 0.375          # Endeudamiento: 300M / 800M
        assert ratios["net_margin"] == 0.2            # Margen Neto: 200M / 1000M
        assert ratios["confidence_level"] == "ALTA"
```

#### 📍 Ruta 3: [test_auth.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/accounts/tests/test_auth.py#L40-L63)
```python
    def test_login_success_and_cookie_jwt_auth_aaa(self):
        # Arrange: Endpoint y credenciales
        url = reverse("auth-login")
        login_credentials = {"email": "analista@banco.com", "password": "Password123!"}

        # Act: Solicitud de inicio de sesión
        response = self.client.post(url, login_credentials, format="json")

        # Assert: Estado 200 y presencia de tokens
        assert response.status_code == 200
        assert "access" in response.data
        assert "access_token" in response.cookies
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 1 refactorizamos todas las pruebas para eliminar tests desordenados con llamadas encadenadas. En `test_validators.py`, `test_ratios.py` y `test_auth.py` delimitamos con comentarios `# Arrange`, `# Act` y `# Assert` cada paso, asegurando que cada prueba sea atómica, legible e independiente."*

---

<!-- slide -->
# 🎯 Diapositiva 4: Semana 2 — Valores Límite (BVA) y Parametrización DRY

### El Requisito
* Aplicar **Análisis de Valores Límite (Boundary Value Analysis - BVA)**.
* Usar `@pytest.mark.parametrize` para inyectar múltiples casos en una sola función (principio DRY).
* Comprobar entradas inválidas y excepciones esperadas mediante `pytest.raises`.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [test_validators.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/companies/tests/test_validators.py#L65-L95) — BVA en Longitud de NIT Colombiano [6, 12]
```python
# Fronteras válidas: Límite inferior exacto (6), +1 (7), -1 (11) y superior exacto (12)
@pytest.mark.parametrize("boundary_nit_digits", ["100000", "1000000", "12345678901", "123456789012"])
def test_validate_and_clean_nit_bva_valid_boundaries(boundary_nit_digits: str):
    # Arrange
    nit_input = boundary_nit_digits
    # Act
    formatted_nit, dv = validate_and_clean_nit(nit_input)
    # Assert
    assert formatted_nit.startswith(nit_input)
    assert len(dv) == 1

# Fronteras inválidas: Límite inferior - 1 (5 dígitos), < 5 (4 dígitos), Límite superior + 1 (13 dígitos)
@pytest.mark.parametrize("invalid_boundary_nit", ["12345", "1234", "1234567890123"])
def test_validate_and_clean_nit_bva_invalid_boundaries(invalid_boundary_nit: str):
    # Arrange
    out_of_bounds_nit = invalid_boundary_nit
    # Act & Assert: Rechazo con excepción ValidationError
    with pytest.raises(ValidationError) as excinfo:
        validate_and_clean_nit(out_of_bounds_nit)
    assert "longitud del NIT es inválida" in str(excinfo.value)
```

#### 📍 Ruta 2: [test_ratios.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/financials/tests/test_ratios.py#L12-L35) — BVA en División Segura
```python
@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (100, 20, 5.0),          # División estándar
        (100, 0, None),          # Límite crítico: Denominador cero
        (0, 100, 0.0),           # Límite: Numerador cero
        (None, 50, None),        # Entrada nula
        (-100, 20, -5.0),        # Valores negativos
        (1, 3, 0.3333),          # Redondeo exacto a 4 decimales
        (0.0001, 10000, 0.0),    # Valor infinitesimal de frontera
    ],
)
def test_safe_divide_bva_parametrized(numerator, denominator, expected):
    # Arrange, Act & Assert en un solo flujo DRY
    assert safe_divide(numerator, denominator) == expected
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 2 aplicamos BVA. Las funciones no fallan en los casos comunes, fallan en las fronteras. En `test_validators.py` probamos con `@pytest.mark.parametrize` los límites de 5, 6, 12 y 13 dígitos de longitud de NIT, y en `test_ratios.py` probamos denominadores en cero, nulos e infinitesimales, verificando excepciones con `pytest.raises`."*

---

<!-- slide -->
# 🛡️ Diapositiva 5: Semana 3 — Cobertura y Quality Gates (`--cov-fail-under=80`)

### El Requisito
* Implementar medición de cobertura con **`pytest-cov`**.
* Configurar `pytest.ini` con una puerta de calidad que obligue a un mínimo de cobertura del 80% usando `--cov-fail-under=80`.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [backend/pytest.ini](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/pytest.ini#L1-L5)
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.local
python_files = tests.py test_*.py *_tests.py
pythonpath = . ..
addopts = --nomigrations --cov=apps --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=80
```

#### 📍 Ruta 2: [backend/requirements.txt](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/requirements.txt#L24-L27)
```text
# Testing & Quality
pytest>=8.3.2,<8.4.0
pytest-django>=4.8.0,<4.9.0
pytest-cov>=5.0.0,<5.1.0
ruff>=0.6.0,<0.7.0
```

### Comportamiento del Quality Gate en Consola
```text
---------- coverage: platform linux, python 3.11.10 -----------
Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
apps/companies/validators.py                 32      0   100%
apps/financials/ratios.py                    45      2    95%   58-59
apps/scoring/services.py                     88      8    91%   112-120
-----------------------------------------------------------------------
TOTAL                                       820    110    86.5%

Required test coverage of 80% reached. Total coverage: 86.5%
Exit Code: 0 (PASSED)
```
*(Si la cobertura total fuera 79.9%, pytest emitiría: `FAIL Required test coverage of 80% not reached` y código de salida 1).*

> 🎤 **Guion del Expositor:**  
> *"En la Semana 3 blindamos la cobertura. Antes, `pytest.ini` medía cobertura pero permitía pasar con cualquier porcentaje. Ahora, con `--cov-fail-under=80`, si el código no alcanza al menos el 80% de cobertura, la ejecución falla automáticamente con Exit Code 1 tanto en local como en el pipeline."*

---

<!-- slide -->
# 🐳 Diapositiva 6: Semana 4 — Contenerización Inmutable de QA

### El Requisito
* Entorno de pruebas aislado con un Dockerfile ligero (`python:3.11-slim`).
* Orquestado con `docker-compose.yml` para ejecución inmutable (cero dependencias locales) retornando **Exit Code 0** si es exitosa.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [docker/backend.Dockerfile](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/docker/backend.Dockerfile#L1-L18)
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt
```

#### 📍 Ruta 2: [docker-compose.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/docker-compose.yml#L53-L73) — Servicio `test` de QA
```yaml
  # Entorno aislado de pruebas QA: Ejecución inmutable y retorno de Exit Code 0
  test:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    container_name: prestamos_qa_runner
    depends_on:
      db:
        condition: service_healthy
      localstack:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.local
      DB_HOST: db
      DB_PORT: 5432
      AWS_ENDPOINT_URL: http://localstack:4566
    command: ["pytest", "--nomigrations", "--cov=apps", "--cov-report=term-missing", "--cov-fail-under=80"]
```

### Comando de Verificación Inmutable
```bash
docker compose run --rm test
# Salida: Ejecuta todas las pruebas dentro del contenedor aislado -> Exit Code 0
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 4 resolvimos la paridad de entornos. Usamos la imagen ligera `python:3.11-slim` y creamos en `docker-compose.yml` el servicio `test`. Con solo ejecutar `docker compose run --rm test`, se levanta PostgreSQL y LocalStack en contenedores y se corren las pruebas sin necesidad de tener Python instalado en la máquina anfitriona."*

---

<!-- slide -->
# 📜 Diapositiva 7: Semana 5 — Pruebas de API y Validación de Contratos JSON Schema

### El Requisito
* Probar endpoints de la API utilizando la librería **`requests`**.
* Verificar códigos de estado HTTP (`200`, `401`, `404`).
* Validar el contrato de datos de las respuestas verificando su estructura con la librería **`jsonschema`**.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [backend/requirements.txt](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/requirements.txt#L28)
```text
jsonschema>=4.20.0,<5.0.0
```

#### 📍 Ruta 2: [test_api_contracts.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/scoring/tests/test_api_contracts.py#L20-L75) — Contratos JSON y Tests con `requests`
```python
# 1. Definición formal del contrato JSON Schema (Draft-07)
HEALTH_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["status", "database", "version"],
    "properties": {
        "status": {"type": "string", "enum": ["ok", "degraded"]},
        "database": {"type": "string", "enum": ["up", "down"]},
        "version": {"type": "string"},
    },
    "additionalProperties": False,
}

# 2. Prueba HTTP real con requests validando el contrato
def test_health_check_endpoint_contract_with_requests(self, live_server):
    # Arrange
    url = f"{live_server.url}/api/v1/health/"

    # Act: Consumo HTTP real sobre el servidor en vivo
    response = requests.get(url, timeout=5)

    # Assert: Código HTTP 200 y validación formal de estructura
    assert response.status_code == 200
    jsonschema.validate(instance=response.json(), schema=HEALTH_CONTRACT_SCHEMA)

# 3. Verificación de códigos HTTP de error
def test_non_existent_endpoint_returns_404(self, live_server):
    response = requests.get(f"{live_server.url}/api/v1/non-existent-route-404/", timeout=5)
    assert response.status_code == 404
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 5 implementamos pruebas de contrato. Usamos `requests` contra `live_server` y validamos que la respuesta cumpla con `HEALTH_CONTRACT_SCHEMA` usando `jsonschema.validate()`. Si algún día un desarrollador renombra un campo o cambia el tipo de dato, el test de contrato falla inmediatamente antes de romper a los clientes de la API."*

---

<!-- slide -->
# 🚀 Diapositiva 8: Semana 6 — Integración Continua (CI) con Docker Compose

### El Requisito
* Pipeline automatizado en GitHub Actions en **`.github/workflows/ci.yml`**.
* Levantar el entorno con **Docker Compose** y ejecutar los tests ante cada `push` o `pull_request`.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [.github/workflows/ci.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/.github/workflows/ci.yml#L1-L45)
```yaml
name: CI - Quality & Docker Compose Tests

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test-and-lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11 (for fast linting)
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run Ruff static linting
        run: pip install ruff && ruff check backend/

      # Levantamiento de entorno y ejecución inmutable con Docker Compose
      - name: Build & Run Tests in Isolated QA Container with Docker Compose
        run: |
          echo "=== [CI] Levantando entorno contenerizado y ejecutando pruebas ==="
          docker compose build test
          docker compose run --rm test

      - name: Tear down Docker Compose environment
        if: always()
        run: docker compose down -v
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 6 llevamos la contenerización al servidor de CI. En `.github/workflows/ci.yml` no instalamos las dependencias directo en la máquina virtual de GitHub; ejecutamos `docker compose run --rm test`. El pipeline levanta los contenedores en Ubuntu, corre los tests con la compuerta del 80% y garantiza Exit Code 0 antes de permitir un merge."*

---

<!-- slide -->
# 🔍 Diapositiva 9: Semana 7 — Análisis Estático de Código con SonarCloud

### El Requisito
* Pipeline dedicado (`sonar.yml`) que integre el análisis estático preventivo con **SonarCloud**.
* Detección de Code Smells, vulnerabilidades de seguridad, código duplicado y deuda técnica antes de llegar a producción.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [.github/workflows/sonar.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/.github/workflows/sonar.yml#L1-L40)
```yaml
name: SonarCloud Static Code Analysis

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  sonarcloud-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - name: Run Pytest with coverage XML for SonarCloud
        working-directory: backend
        run: pytest --cov=apps --cov-report=xml:coverage.xml --cov-fail-under=80

      - name: SonarCloud Scan
        if: ${{ secrets.SONAR_TOKEN != '' }}
        uses: SonarSource/sonarqube-scan-action@v4
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

#### 📍 Ruta 2: [sonar-project.properties](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/sonar-project.properties#L1-L11)
```properties
sonar.projectKey=DMaTeoG_prestamos_pruebas
sonar.organization=dmateog
sonar.sources=backend
sonar.tests=backend
sonar.test.inclusions=**/tests/**,**/test_*.py
sonar.exclusions=**/migrations/**,**/__pycache__/**,ml/data/**
sonar.python.version=3.11
sonar.python.coverage.reportPaths=backend/coverage.xml
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 7 creamos el pipeline `sonar.yml` y configuramos `sonar-project.properties`. SonarCloud analiza la seguridad estática, buscando vulnerabilidades OWASP Top 10, inyecciones de código y deuda técnica, alimentándose directamente del informe `coverage.xml`."*

---

<!-- slide -->
# 📈 Diapositiva 10: Semana 8 — Pruebas de Carga y Rendimiento (Locust)

### El Requisito
* Script **`locustfile.py`** con Locust para emular tráfico masivo concurrente.
* Evaluar comportamiento bajo estrés midiendo **Latencia** y **Requests Per Second (RPS)**.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [tests/performance/locustfile.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/tests/performance/locustfile.py#L12-L55) — Simulación Concurrente
```python
class ScoringBackendUser(HttpUser):
    """Simula un analista interactuando con la API bajo carga concurrente."""
    wait_time = between(0.5, 2.0)
    authenticated = False

    @task(5)
    def check_health(self) -> None:
        """Verificación de disponibilidad de la base de datos y backend."""
        self.client.get("/api/v1/health/", name="GET /api/v1/health/")

    @task(3)
    def list_evaluations(self) -> None:
        """Consulta paginada de evaluaciones."""
        if self.authenticated:
            self.client.get("/api/v1/evaluations/", name="GET /api/v1/evaluations/")

    @task(2)
    def lookup_company(self) -> None:
        """Búsqueda y consulta de NITs de empresas."""
        if self.authenticated:
            self.client.get(f"/api/v1/companies/lookup/?nit={TEST_NIT}", name="GET /api/v1/companies/lookup/")
```

#### 📍 Ruta 2: [tests/performance/locust_smoke.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/tests/performance/locust_smoke.py#L6-L13) — Smoke Test Rápido
```python
class HealthSmokeUser(HttpUser):
    wait_time = between(0.2, 0.5)
    @task
    def health(self) -> None:
        self.client.get("/api/v1/health/", name="GET /api/v1/health/")
```

#### 📍 Ruta 3: [docker-compose.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/docker-compose.yml#L75-L89) — Servicio Locust
```yaml
  locust:
    image: locustio/locust:2.32.4
    container_name: prestamos_locust
    profiles: ["perf"]
    ports: ["8089:8089"]
    command: -f /mnt/locust/locustfile.py --host http://backend:8000
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 8 implementamos `locustfile.py`. Con tareas ponderadas mediante `@task(5)`, `@task(3)` y `@task(2)`, simulamos analistas autenticados consultando la API en masa. Esto permite medir la latencia percentil p95 y los Requests Per Second (RPS) tanto en interfaz web como en modo headless para el pipeline."*

---

<!-- slide -->
# 🔄 Diapositiva 11: Semana 9 — CD, Validaciones en Staging, Rollback y Telegram

### El Requisito
* Pipeline de CD automatizado en GitHub Actions con **Smoke Tests en Staging** antes de pasar a Producción.
* Script de despliegue (**`deploy.py`**) con lógica de **Rollback automático** ante fallo (HTTP 500).
* Integración de telemetría móvil en tiempo real vía **Telegram Bot**.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [scripts/deploy.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/scripts/deploy.py#L42-L75) — Lógica de Despliegue y Rollback ante HTTP 500
```python
def execute_rollback(image_name: str, environment: str, app_version: str, reason: str):
    """Restaura automáticamente el contenedor a la imagen estable previa :previous."""
    print(f"⚠️ [CD-ROLLBACK] INICIANDO ROLLBACK AUTOMÁTICO: {reason}")
    run_command(["docker", "tag", f"{image_name}:previous", f"{image_name}:latest"])
    env = os.environ.copy()
    env["APP_VERSION"] = "previous"
    subprocess.run(["docker", "compose", "up", "-d", "backend"], env=env)
    notify_telegram(
        title=f"CD Rollback Automático [{environment.upper()}]",
        status="ROLLBACK", version=app_version,
        details=f"Fallo detectado ({reason}). Contenedor restaurado a versión estable :previous"
    )

def deploy(stage: str, app_version: str, health_url: str) -> int:
    # 1. Respaldar imagen previa :latest -> :previous
    run_command(["docker", "tag", "prestamos-backend:latest", "prestamos-backend:previous"])
    # 2. Desplegar nueva versión
    subprocess.run(["docker", "compose", "up", "-d", "db", "backend"])
    # 3. Sondeo del Healthcheck
    healthy, code, details = check_health(health_url)
    if healthy:
        notify_telegram(title=f"CD Despliegue Exitoso [{stage.upper()}]", status="SUCCESS", version=app_version, details="Healthcheck 200 OK")
        return 0
    # 4. Si falla (HTTP 500) -> Rollback inmediato
    execute_rollback("prestamos-backend", stage, app_version, f"HTTP Error {code}")
    return 1
```

#### 📍 Ruta 2: [scripts/notify_telegram.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/scripts/notify_telegram.py#L27-L49) — Bot de Telemetría
```python
def send_telegram_message(message: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return 200 <= resp.status < 300
```

#### 📍 Ruta 3: [.github/workflows/cd-rollback.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/.github/workflows/cd-rollback.yml#L15-L55) — Pipeline Staging $\rightarrow$ Producción
```yaml
jobs:
  staging-verify:
    name: Staging Deployment & Smoke Testing
    steps:
      - run: python scripts/deploy.py --stage staging
      - name: Run Automated Smoke Tests in Staging (Locust)
        run: locust -f tests/performance/locust_smoke.py --headless --users 5 --run-time 15s --host http://localhost:8000

  production-deploy:
    name: Production Continuous Deployment
    needs: staging-verify # Solo pasa a producción si Staging supera los Smoke Tests
    steps:
      - run: python scripts/deploy.py --stage prod
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 9 creamos `deploy.py` y `cd-rollback.yml`. Primero desplegamos en Staging y corremos smoke tests con Locust. Si Staging pasa, se promueve a Producción. Antes de actualizar, se respalda la imagen `:latest` como `:previous`. Si el healthcheck detecta un error HTTP 500, se revierte automáticamente a `:previous` y se envía una alerta inmediata a Telegram."*

---

<!-- slide -->
# ☁️ Diapositiva 12: Semana 10 — Infraestructura como Código (IaC) con LocalStack y Boto3

### El Requisito
* Aprovisionamiento declarativo mediante Docker Compose y **LocalStack** para emular servicios AWS en local.
* Creación de **buckets S3** y **colas SQS** con un script de inicialización utilizando **`boto3`**.

---

### Rutas de Archivos y Fragmentos de Código

#### 📍 Ruta 1: [docker-compose.yml](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/docker-compose.yml#L19-L34) — Servicio LocalStack
```yaml
  localstack:
    image: localstack/localstack:3.0
    container_name: prestamos_localstack
    ports: ["4566:4566"]
    environment:
      - SERVICES=s3,sqs
      - DOCKER_HOST=unix:///var/run/docker.sock
      - AWS_DEFAULT_REGION=us-east-1
    volumes:
      - ./scripts/init_localstack.py:/etc/localstack/init/ready.d/init_aws.py
      - localstack_data:/var/lib/localstack
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:4566/_localstack/health"]
```

#### 📍 Ruta 2: [scripts/init_localstack.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/scripts/init_localstack.py#L30-L65) — Aprovisionamiento con Boto3
```python
def provision_s3_bucket(s3_client, bucket_name: str, region: str) -> str:
    """Crea de forma idempotente el bucket S3 para almacenamiento de documentos."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"[IaC-LocalStack] Bucket S3 '{bucket_name}' aprovisionado exitosamente.")
    return bucket_name

def provision_sqs_queues(sqs_client, queue_name: str, dlq_name: str) -> dict:
    """Crea colas SQS principal y Dead Letter Queue (DLQ)."""
    dlq_res = sqs_client.create_queue(QueueName=dlq_name, Attributes={"MessageRetentionPeriod": "1209600"})
    queue_res = sqs_client.create_queue(QueueName=queue_name, Attributes={"VisibilityTimeout": "60"})
    return {"main_queue_url": queue_res["QueueUrl"], "dlq_url": dlq_res["QueueUrl"]}
```

#### 📍 Ruta 3: [test_localstack_aws.py](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/apps/sources/tests/test_localstack_aws.py#L18-L45) — Pruebas de IaC
```python
class TestLocalStackAwsProvisioning:
    def test_provision_s3_bucket_creates_when_not_exists_aaa(self):
        # Arrange
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")
        # Act
        result_bucket = provision_s3_bucket(mock_s3, "test-empresa-documentos-bucket", "us-east-1")
        # Assert
        assert result_bucket == "test-empresa-documentos-bucket"
        mock_s3.create_bucket.assert_called_once_with(Bucket="test-empresa-documentos-bucket")
```

#### 📍 Ruta 4: [backend/requirements.txt](file:///c:/Pruebas%20y%20Mantenimiento/prestamos_pruebas/backend/requirements.txt#L31)
```text
boto3>=1.34.0,<2.0.0
```

> 🎤 **Guion del Expositor:**  
> *"En la Semana 10 cerramos con IaC. Levantamos LocalStack 3.0 en Docker Compose en el puerto 4566. Con `init_localstack.py` usamos `boto3` para crear el bucket S3 `prestamos-documentos-bucket` y las colas SQS con su DLQ. Y en `test_localstack_aws.py` validamos bajo el patrón AAA que el aprovisionamiento sea idempotente y tolerante a fallos."*

---

<!-- slide -->
# 📊 Diapositiva 13: Matriz de Trazabilidad Integral — Estado Inicial vs. Estado Actual

| Semana | Requisito Técnico Auditado | Estado Inicial | Estado Actual | Archivos Principales y Rutas |
|:---:|---|:---:|:---:|---|
| **S1** | Pruebas Unitarias y Patrón AAA | ⚠️ Parcial | ✅ **100%** | `backend/apps/*/tests/` (`test_validators.py`, `test_ratios.py`, `test_auth.py`) |
| **S2** | BVA y Parametrización DRY | ⚠️ Parcial | ✅ **100%** | `test_validators.py`, `test_ratios.py` (`@pytest.mark.parametrize`, `pytest.raises`) |
| **S3** | Cobertura y Quality Gates | ⚠️ Parcial | ✅ **100%** | `backend/pytest.ini` (`--cov-fail-under=80`), `requirements.txt` (`pytest-cov`) |
| **S4** | Contenerización QA Inmutable | ⚠️ Parcial | ✅ **100%** | `docker/backend.Dockerfile` (`python:3.11-slim`), `docker-compose.yml` (servicio `test`) |
| **S5** | Pruebas de API y JSON Schema | ❌ No Cumple | ✅ **100%** | `test_api_contracts.py` (`requests`, `jsonschema.validate`, HTTP 200, 401, 404) |
| **S6** | CI con Docker Compose | ⚠️ Parcial | ✅ **100%** | `.github/workflows/ci.yml` (`docker compose build/run test`) |
| **S7** | Análisis Estático SonarCloud | ✅ Cumple | ✅ **100%** | `.github/workflows/sonar.yml`, `sonar-project.properties` |
| **S8** | Pruebas de Carga (Locust) | ✅ Cumple | ✅ **100%** | `tests/performance/locustfile.py`, `locust_smoke.py` (latencia p95, RPS) |
| **S9** | CD, Staging, Rollback y Telegram | ⚠️ Parcial | ✅ **100%** | `scripts/deploy.py`, `.github/workflows/cd-rollback.yml`, `scripts/notify_telegram.py` |
| **S10**| IaC LocalStack AWS con Boto3 | ❌ No Cumple | ✅ **100%** | `docker-compose.yml` (`localstack`), `scripts/init_localstack.py`, `test_localstack_aws.py` |

> 🎤 **Guion del Expositor:**  
> *"Esta tabla resume el antes y el después de la auditoría. Los puntos que estaban en rojo (Semana 5 y Semana 10) y los que estaban parciales (Semanas 1, 2, 3, 4, 6 y 9) fueron subsanados con código verificado y enlazado en la matriz de trazabilidad."*

---

<!-- slide -->
# 🏆 Diapositiva 14: Conclusiones y Demostración en Vivo

### Logros Clave para la Organización
1. **Calidad Blindada por Defecto:** Ningún código llega a la rama principal si no cumple el 80% de cobertura y la estructura AAA/BVA.
2. **Contratos Protegidos:** Las pruebas con `requests` y `jsonschema` impiden que cambios inesperados en la API afecten a los clientes frontend.
3. **Resiliencia con Cero Tiempo de Inactividad:** Ante errores HTTP 500 en producción, `deploy.py` revierte automáticamente a la versión `:previous` y emite telemetría instantánea a Telegram.
4. **Desarrollo Cloud Local sin Costos:** Con LocalStack y Boto3 emulamos S3 y SQS localmente con total fidelidad a AWS.

```text
================================================================================
           AUDITORÍA TÉCNICA QA & DEVSECOPS CONCLUIDA EXITOSAMENTE
                    CALIFICACIÓN: 10/10 SEMANAS (100%)
================================================================================
```

### Comandos Rápidos para Demostración en Vivo:
* **Ejecutar Pruebas Contenerizadas con Quality Gate:**
  ```bash
  docker compose run --rm test
  ```
* **Aprovisionar S3 y SQS en LocalStack:**
  ```bash
  python scripts/init_localstack.py
  ```
* **Simular Despliegue con Rollback Automático:**
  ```bash
  python scripts/deploy.py --stage prod --simulate-failure
  ```

> 🎤 **Guion del Expositor:**  
> *"Con esto concluimos la presentación técnica. El repositorio se encuentra 100% operable, documentado y listo para ser demostrado en vivo o inspeccionado en GitHub. Muchas gracias por su atención."*
