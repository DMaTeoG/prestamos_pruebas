import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminUserRole
from apps.accounts.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.audit.models import AuditAction
from apps.audit.services import log_action

logger = logging.getLogger("apps.accounts.views")


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            user_data = response.data.get("user", {})
            user_id = user_data.get("id")

            user_obj = CustomUser.objects.filter(pk=user_id).first() if user_id else None
            if user_obj:
                log_action(
                    user=user_obj,
                    action=AuditAction.USER_LOGIN,
                    entity="CustomUser",
                    entity_id=user_obj.id,
                    request=request,
                    metadata={"role": user_obj.role},
                )
                logger.info("User login successful: user_id=%s role=%s", user_obj.id, user_obj.role)

            # Set httpOnly cookies (SameSite=None + Secure=True in production for cross-domain Vercel <-> Render)
            cookie_samesite = "Lax" if settings.DEBUG else "None"
            cookie_secure = not settings.DEBUG
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=3600,
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                samesite=cookie_samesite,
                secure=cookie_secure,
                max_age=7 * 24 * 3600,
            )
        return response


class CustomRefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if not refresh_token:
            logger.warning("Token refresh failed: missing refresh_token")
            return Response(
                {"code": "MISSING_REFRESH_TOKEN", "message": "No se proporcionó token de refresco."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            logger.warning("Token refresh failed: %s", exc.__class__.__name__)
            return Response(
                {"code": "INVALID_REFRESH_TOKEN", "message": "Token de refresco inválido o expirado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        response = Response(data, status=status.HTTP_200_OK)
        cookie_samesite = "Lax" if settings.DEBUG else "None"
        cookie_secure = not settings.DEBUG
        response.set_cookie(
            key="access_token",
            value=data.get("access"),
            httponly=True,
            samesite=cookie_samesite,
            secure=cookie_secure,
            max_age=3600,
        )
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh_token") or request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as exc:
            logger.debug("Logout token blacklist skipped: %s", exc.__class__.__name__)

        logger.info("User logged out: user_id=%s", request.user.id)
        response = Response(
            {"message": "Sesión cerrada correctamente."},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class AdminUserListView(generics.ListAPIView):
    """GET /api/v1/admin/users/ — Lista todos los usuarios (solo Administrador)."""

    permission_classes = [IsAdminUserRole]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all().order_by("-created_at")
    pagination_class = None


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """PATCH /api/v1/admin/users/<pk>/ — Actualiza rol o estado activo de un usuario."""

    permission_classes = [IsAdminUserRole]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

    def perform_update(self, serializer):
        updated_user = serializer.save()
        logger.info(
            "Admin user_id=%s updated user_id=%s (role=%s, is_active=%s)",
            self.request.user.id,
            updated_user.id,
            updated_user.role,
            updated_user.is_active,
        )
