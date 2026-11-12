from django.urls import path

from apps.reports.views import EvaluationReportPDFView
from apps.scoring.views import EvaluationDetailView, EvaluationListCreateView

urlpatterns = [
    path("", EvaluationListCreateView.as_view(), name="evaluation-list-create"),
    path("<int:pk>/", EvaluationDetailView.as_view(), name="evaluation-detail"),
    path("<int:pk>/report.pdf", EvaluationReportPDFView.as_view(), name="evaluation-report-pdf"),
]
