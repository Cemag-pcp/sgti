from django.db import models


class Application(models.Model):
    INTERNAL = 'INTERNAL'
    EXTERNAL = 'EXTERNAL'
    TYPE_CHOICES = [
        (INTERNAL, 'Interno'),
        (EXTERNAL, 'Externo'),
    ]

    name = models.CharField(max_length=120, unique=True, verbose_name='Nome')
    app_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Tipo')
    responsible = models.CharField(max_length=120, blank=True, verbose_name='Responsável')
    url = models.URLField(blank=True, verbose_name='URL')
    release_date = models.DateField(null=True, blank=True, verbose_name='Data de lançamento')
    description = models.TextField(verbose_name='Descrição')
    notes = models.TextField(blank=True, verbose_name='Observações')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aplicativo'
        verbose_name_plural = 'Aplicativos'
        ordering = ['name']

    def __str__(self):
        return self.name
