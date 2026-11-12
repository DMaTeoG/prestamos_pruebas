from django.urls import path
from apps.scoring.views import EvaluationListCreateView, EvaluationDetailView
from apps.reports.views import EvaluationReportPDFView

urlpatterns = [
    path("", EvaluationListCreateView.as_view(), name="evaluation-list-create"),
    path("<int:pk>/", EvaluationDetailView.as_view(), name="evaluation-detail"),
    path("<int:pk>/report.pdf", EvaluationReportPDFView.as_view(), name="evaluation-report-pdf"),
]
