from django.urls import path, include
from apps.companies.views import CompanyLookupView, CompanyDetailView, MyCompanyView

urlpatterns = [
    path("lookup/", CompanyLookupView.as_view(), name="company-lookup"),
    path("my-company/", MyCompanyView.as_view(), name="company-my-company"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<int:company_id>/financial-statements/", include("apps.financials.urls")),
]
