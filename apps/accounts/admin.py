from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, RequesterProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'full_name']
    ordering = ['full_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('full_name', 'role')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(RequesterProfile)
class RequesterProfileAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'full_name', 'email', 'phone', 'created_at']
    search_fields = ['matricula', 'full_name', 'email']
    ordering = ['full_name']
