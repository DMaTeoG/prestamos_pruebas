#!/usr/bin/env python3
"""Script de Despliegue Continuo (CD) con Rollback Automático y Telemetría en Telegram (Semana 9).

Funcionalidades:
1. Guarda la imagen previa `:latest` como `:previous` para permitir reversión inmediata.
2. Construye e inicia el nuevo contenedor para el entorno (Staging / Producción).
3. Monitorea el endpoint de salud (Healthcheck HTTP 200).
4. Si detecta fallo (HTTP 500, timeout o error de conexión):
   - Ejecuta ROLLBACK automático restaurando la imagen `:previous`.
   - Notifica en tiempo real vía Telegram con estado ROLLBACK.
   - Retorna código de salida 1.
5. Si el despliegue es exitoso:
   - Notifica en tiempo real vía Telegram con estado SUCCESS.
   - Retorna código de salida 0.
"""

import os
import sys
import time
import argparse
import subprocess
import urllib.request
import urllib.error


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Ejecuta un comando en el sistema y retorna el resultado."""
    print(f"[CD-Deploy] Ejecutando: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)  # NOSONAR


def notify_telegram(title: str, status: str, version: str, details: str):
    """Invoca el script de telemetría de Telegram."""
    telegram_script = os.path.join(os.path.dirname(__file__), "notify_telegram.py")
    if os.path.exists(telegram_script):
        cmd = [
            sys.executable,
            telegram_script,
            "--title", title,
            "--status", status,
            "--version", version,
            "--details", details,
        ]
        subprocess.run(cmd, check=False)  # NOSONAR


def check_health(health_url: str, retries: int = 15, delay: float = 2.0) -> tuple[bool, int, str]:
    """Sondea el endpoint de salud verificando si responde HTTP 200."""
    print(f"[CD-Deploy] Verificando salud en {health_url} (máx {retries} intentos)...")
    if not (health_url.startswith("http://localhost") or health_url.startswith("http://127.0.0.1")):
        print("[CD-Deploy] URL de healthcheck no permitida.")
        return False, 400, "Invalid host"

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "CD-HealthCheck/1.0"})  # NOSONAR
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.getcode()
                body = response.read().decode("utf-8")
                if status_code == 200:
                    print(f"[CD-Deploy] Healthcheck exitoso (HTTP 200) en intento {attempt}/{retries}.")
                    return True, status_code, body
        except urllib.error.HTTPError as http_err:
            print(f"[CD-Deploy] Intento {attempt}/{retries}: HTTP Error {http_err.code}")
            if http_err.code >= 500:
                return False, http_err.code, http_err.reason
        except Exception as exc:
            print(f"[CD-Deploy] Intento {attempt}/{retries}: Conexión en espera ({exc})...")
        time.sleep(delay)
    return False, 500, "Timeout superado sin respuesta exitosa"


def execute_rollback(image_name: str, environment: str, app_version: str, reason: str):
    """Ejecuta la restauración automática a la imagen anterior."""
    print("=================================================================")
    print("⚠️  [CD-ROLLBACK] INICIANDO ROLLBACK AUTOMÁTICO INMEDIATO")
    print(f"⚠️  Razón del fallo: {reason}")
    print("=================================================================")

    # 1. Re-etiquetar imagen previous como latest
    run_command(["docker", "tag", f"{image_name}:previous", f"{image_name}:latest"])

    # 2. Reiniciar contenedor con la versión anterior
    env = os.environ.copy()
    env["APP_VERSION"] = "previous"
    subprocess.run(["docker", "compose", "up", "-d", "backend"], env=env)

    # 3. Notificar a Telegram
    notify_telegram(
        title=f"CD Rollback Automático [{environment.upper()}]",
        status="ROLLBACK",
        version=app_version,
        details=f"Fallo detectado ({reason}). Contenedor restaurado a versión estable :previous",
    )


def deploy(stage: str, app_version: str, health_url: str, simulate_failure: bool = False) -> int:
    image_name = "prestamos-backend"
    print(f"=== [CD] Iniciando despliegue de versión '{app_version}' en entorno: {stage.upper()} ===")

    # 1. Respaldar versión previa si existe
    inspect = run_command(["docker", "image", "inspect", f"{image_name}:latest"])
    has_previous = inspect.returncode == 0
    if has_previous:
        print(f"[CD] Respaldando {image_name}:latest -> {image_name}:previous")
        run_command(["docker", "tag", f"{image_name}:latest", f"{image_name}:previous"])

    # 2. Construir imagen de la nueva versión
    build_res = run_command([
        "docker", "build",
        "-f", "docker/backend.Dockerfile",
        "-t", f"{image_name}:{app_version}",
        "-t", f"{image_name}:latest",
        ".",
    ])
    if build_res.returncode != 0:
        print(f"[CD][ERROR] Falló la construcción de la imagen:\n{build_res.stderr}")
        notify_telegram(
            title=f"CD Fallo de Construcción [{stage.upper()}]",
            status="FAILED",
            version=app_version,
            details="Error al compilar Dockerfile en el paso de build.",
        )
        return 1

    # 3. Levantar servicios
    env = os.environ.copy()
    env["APP_VERSION"] = app_version
    subprocess.run(["docker", "compose", "up", "-d", "db", "backend"], env=env)

    # Si se solicitó simular fallo deliberado (ej. para pruebas en GitHub Actions)
    if simulate_failure:
        print("[CD-TEST] SIMULANDO FALLO CRÍTICO (HTTP 500)...")
        target_health_url = "http://localhost:8000/api/v1/force-failure-500/"
    else:
        target_health_url = health_url

    # 4. Verificación de Healthcheck
    healthy, code, details = check_health(target_health_url)

    if healthy:
        print(f"=== [CD] Despliegue en {stage.upper()} COMPLETADO EXITOSAMENTE ===")
        notify_telegram(
            title=f"CD Despliegue Exitoso [{stage.upper()}]",
            status="SUCCESS",
            version=app_version,
            details=f"Healthcheck HTTP 200 verificado en {target_health_url}",
        )
        return 0

    # 5. Fallo detectado -> Ejecutar Rollback
    if has_previous:
        execute_rollback(image_name, stage, app_version, f"HTTP Status {code}: {details}")
    else:
        print("[CD][ERROR] No existe imagen previa para realizar rollback.")
        notify_telegram(
            title=f"CD Fallo Crítico [{stage.upper()}]",
            status="FAILED",
            version=app_version,
            details=f"Falló healthcheck ({code}) y no hay imagen :previous disponible",
        )
    return 1


def main():
    parser = argparse.ArgumentParser(description="CD Deploy con Rollback y Telemetría")
    parser.add_argument("--stage", default="staging", choices=["staging", "prod"], help="Entorno de despliegue")
    parser.add_argument("--version", default=os.getenv("APP_VERSION", "v1.0.0"), help="Versión / Git SHA")
    parser.add_argument("--health-url", default="http://localhost:8000/api/v1/health/", help="URL del healthcheck")
    parser.add_argument("--simulate-failure", action="store_true", help="Simula fallo HTTP 500 para probar rollback")
    args = parser.parse_args()

    exit_code = deploy(
        stage=args.stage,
        app_version=args.version,
        health_url=args.health_url,
        simulate_failure=args.simulate_failure,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

