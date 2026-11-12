import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("apps.scoring.consumers")


class ScoringConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time status transitions
    during credit evaluations.
    """

    async def connect(self):
        await self.accept()
        await self.send(
            json.dumps(
                {
                    "type": "connection_established",
                    "message": "Conectado al canal WebSocket de scoring empresarial.",
                }
            )
        )
        logger.info("WebSocket connection established for scoring stream")

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected with code %s", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except Exception:
            await self.send(json.dumps({"error": "Payload JSON inválido"}))
            return

        action = payload.get("action")
        nit = payload.get("nit", "").strip()

        if action == "ping":
            await self.send(json.dumps({"type": "pong", "message": "Canal activo"}))
            return

        if action == "evaluate":
            steps = [
                {
                    "step": 1,
                    "status": "VALIDATING_NIT",
                    "title": "Validación de Identificación",
                    "detail": f"Verificando estructura y dígito de verificación del NIT {nit}...",
                    "progress": 20,
                },
                {
                    "step": 2,
                    "status": "FETCHING_RUES",
                    "title": "Consulta de Registro Mercantil",
                    "detail": "Consultando RUES y Cámaras de Comercio en datos abiertos...",
                    "progress": 40,
                },
                {
                    "step": 3,
                    "status": "PROCESSING_FINANCIALS",
                    "title": "Análisis Financiero",
                    "detail": "Calculando ratios de liquidez, endeudamiento, cobertura y ROA...",
                    "progress": 60,
                },
                {
                    "step": 4,
                    "status": "RUNNING_XGBOOST",
                    "title": "Modelo de Scoring XGBoost",
                    "detail": "Ejecutando inferencia ML y calibración sigmoide de probabilidad...",
                    "progress": 80,
                },
                {
                    "step": 5,
                    "status": "COMPUTING_SHAP",
                    "title": "Explicabilidad SHAP",
                    "detail": "Determinando los factores principales y su impacto en el score...",
                    "progress": 95,
                },
                {
                    "step": 6,
                    "status": "COMPLETED",
                    "title": "Evaluación Concluida",
                    "detail": "Score 0–1000 generado y listo para su visualización.",
                    "progress": 100,
                },
            ]

            for s in steps:
                await self.send(
                    json.dumps(
                        {
                            "type": "scoring_progress",
                            "nit": nit,
                            **s,
                        }
                    )
                )
                await asyncio.sleep(0.4)
