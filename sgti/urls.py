from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('assets/', include('apps.assets.urls')),
    path('', RedirectView.as_view(url='/tickets/', permanent=False)),
]
