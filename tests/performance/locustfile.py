"""Locust performance test suite for the Scoring Empresarial backend API."""

import os
from locust import HttpUser, between, task


PERF_USER_EMAIL = os.getenv("PERF_USER_EMAIL", "analyst@example.com")
PERF_USER_PASSWORD = os.getenv("PERF_USER_PASSWORD", "AnalystPass123!")
TEST_NIT = os.getenv("PERF_TEST_NIT", "900123456")


class ScoringBackendUser(HttpUser):
    """Simulates an analyst interacting with the Django REST API."""

    wait_time = between(0.5, 2.0)
    authenticated = False

    def on_start(self) -> None:
        """Authenticate once per virtual user (JWT stored in httpOnly cookies)."""
        with self.client.post(
            "/api/v1/auth/login/",
            json={"email": PERF_USER_EMAIL, "password": PERF_USER_PASSWORD},
            name="POST /api/v1/auth/login/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.authenticated = True
                response.success()
            elif response.status_code in (400, 401):
                # Allow healthcheck-only runs when test user is not seeded yet
                self.authenticated = False
                response.failure(
                    f"Login failed ({response.status_code}). Seed PERF_USER_EMAIL or run healthcheck."
                )

    @task(5)
    def check_health(self) -> None:
        """Baseline availability and DB connectivity check."""
        self.client.get("/api/v1/health/", name="GET /api/v1/health/")

    @task(3)
    def get_profile(self) -> None:
        """Fetch authenticated user profile."""
        if not self.authenticated:
            return
        self.client.get("/api/v1/auth/me/", name="GET /api/v1/auth/me/")

    @task(3)
    def list_evaluations(self) -> None:
        """List evaluations with pagination."""
        if not self.authenticated:
            return
        self.client.get("/api/v1/evaluations/", name="GET /api/v1/evaluations/")

    @task(2)
    def lookup_company(self) -> None:
        """Lookup company by NIT."""
        if not self.authenticated:
            return
        with self.client.get(
            f"/api/v1/companies/lookup/?nit={TEST_NIT}",
            name="GET /api/v1/companies/lookup/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")
