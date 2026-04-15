from django.conf import settings
from django.contrib import admin
from django.http import FileResponse
from django.urls import path, include
from django.views.generic import RedirectView
import os


def serve_sw(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', serve_sw, name='sw_js'),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('assets/', include('apps.assets.urls')),
    path('', RedirectView.as_view(url='/tickets/', permanent=False)),
]
