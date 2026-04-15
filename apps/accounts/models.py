from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.SUPERVISOR)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    SUPERVISOR = 'SUPERVISOR'
    TECHNICIAN = 'TECHNICIAN'
    ROLE_CHOICES = [
        (SUPERVISOR, 'Supervisor'),
        (TECHNICIAN, 'Técnico'),
    ]

    email = models.EmailField(unique=True, verbose_name='E-mail')
    full_name = models.CharField(max_length=200, verbose_name='Nome completo')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=TECHNICIAN, verbose_name='Função')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'

    @property
    def is_supervisor(self):
        return self.role == self.SUPERVISOR

    @property
    def is_technician(self):
        return self.role in (self.SUPERVISOR, self.TECHNICIAN)


class RequesterProfile(models.Model):
    matricula = models.CharField(max_length=50, unique=True, verbose_name='Matrícula')
    full_name = models.CharField(max_length=200, verbose_name='Nome completo')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Telefone')
    whatsapp_phone = models.CharField(max_length=30, blank=True, verbose_name='WhatsApp')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Solicitante'
        verbose_name_plural = 'Solicitantes'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.matricula})'
