from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'core'

urlpatterns = [
    path('', RedirectView.as_view(url='/tickets/', permanent=False)),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/create/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_edit'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
]
