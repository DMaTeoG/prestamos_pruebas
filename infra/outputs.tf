output "backend_url" {
  description = "URL del backend desplegado mediante IaC"
  value       = "http://localhost:${var.backend_port}/api/v1/health/"
}

output "network_name" {
  description = "Nombre de la red Docker provisionada"
  value       = docker_network.scoring_network.name
}
