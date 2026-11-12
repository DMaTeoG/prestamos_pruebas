from django.urls import re_path
from apps.scoring.consumers import ScoringConsumer

websocket_urlpatterns = [
    re_path(r"^ws/scoring/$", ScoringConsumer.as_asgi()),
]
