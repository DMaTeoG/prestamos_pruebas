from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    ANALYST = "ANALYST", "Analista"
    COMPANY = "COMPANY", "Empresa"
    ADMIN = "ADMIN", "Administrador"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role=Role.ANALYST, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Correo electrónico", unique=True)
    first_name = models.CharField("Nombres", max_length=150, blank=True)
    last_name = models.CharField("Apellidos", max_length=150, blank=True)
    role = models.CharField(
        "Rol de usuario",
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )
    is_active = models.BooleanField("Activo", default=True)
    is_staff = models.BooleanField("Es staff", default=False)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Fecha de actualización", auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
