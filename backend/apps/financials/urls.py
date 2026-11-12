from django.urls import path
from apps.financials.views import FinancialStatementListCreateView, FinancialStatementCSVImportView

urlpatterns = [
    path("", FinancialStatementListCreateView.as_view(), name="financial-statement-list-create"),
    path("import-csv/", FinancialStatementCSVImportView.as_view(), name="financial-statement-csv-import"),
]
