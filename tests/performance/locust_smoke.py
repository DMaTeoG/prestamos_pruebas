"""Lightweight Locust smoke test for CD health verification."""

from locust import HttpUser, between, task


class HealthSmokeUser(HttpUser):
    """Hits the backend health endpoint to verify container stability under light load."""

    wait_time = between(0.2, 0.5)

    @task
    def health(self) -> None:
        self.client.get("/api/v1/health/", name="GET /api/v1/health/")
