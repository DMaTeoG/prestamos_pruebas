variable "environment" {
  description = "Nombre del entorno (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "backend_image" {
  description = "Imagen Docker del backend a desplegar"
  type        = string
  default     = "prestamos-backend:latest"
}

variable "backend_port" {
  description = "Puerto expuesto del backend"
  type        = number
  default     = 8000
}

variable "db_name" {
  description = "Nombre de la base de datos PostgreSQL"
  type        = string
  default     = "scoring"
}

variable "db_user" {
  description = "Usuario de PostgreSQL"
  type        = string
  default     = "scoring"
}

variable "db_password" {
  description = "Contraseña de PostgreSQL"
  type        = string
  sensitive   = true
  default     = "scoring_password"
}
