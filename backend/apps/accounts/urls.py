from django.urls import path
from apps.accounts.views import (
    LoginView,
    CustomRefreshTokenView,
    LogoutView,
    UserProfileView,
    RegisterView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", CustomRefreshTokenView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", UserProfileView.as_view(), name="auth-me"),
    path("register/", RegisterView.as_view(), name="auth-register"),
]
