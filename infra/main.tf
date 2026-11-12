terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# Red privada para aislar la comunicación backend <-> base de datos
resource "docker_network" "scoring_network" {
  name = "prestamos_network_${var.environment}"
}

# Volumen persistente para PostgreSQL
resource "docker_volume" "postgres_data" {
  name = "prestamos_pg_data_${var.environment}"
}

resource "docker_image" "postgres" {
  name         = "postgres:16-alpine"
  keep_locally = true
}

# Contenedor de Base de Datos PostgreSQL
resource "docker_container" "postgres" {
  name  = "prestamos_db_${var.environment}"
  image = docker_image.postgres.image_id

  networks_advanced {
    name = docker_network.scoring_network.name
    aliases = ["db"]
  }

  env = [
    "POSTGRES_DB=${var.db_name}",
    "POSTGRES_USER=${var.db_user}",
    "POSTGRES_PASSWORD=${var.db_password}",
  ]

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  restart = "unless-stopped"
}

# Contenedor del Backend Django
resource "docker_container" "backend" {
  name  = "prestamos_backend_${var.environment}"
  image = var.backend_image

  depends_on = [docker_container.postgres]

  networks_advanced {
    name = docker_network.scoring_network.name
  }

  ports {
    internal = 8000
    external = var.backend_port
  }

  env = [
    "DJANGO_SETTINGS_MODULE=config.settings.local",
    "DB_NAME=${var.db_name}",
    "DB_USER=${var.db_user}",
    "DB_PASSWORD=${var.db_password}",
    "DB_HOST=db",
    "DB_PORT=5432",
    "ALLOWED_HOSTS=localhost,127.0.0.1",
    "MODEL_ARTIFACT_DIR=/app/ml/artifacts/",
    "APP_VERSION=${var.environment}",
  ]

  restart = "unless-stopped"
}
