from django.urls import path
from . import views

app_name = 'software_requests'

urlpatterns = [
    path('', views.SoftwareRequestSubmitView.as_view(), name='submit'),
    path('gerenciar/', views.SoftwareRequestListView.as_view(), name='list'),
    path('gerenciar/<int:pk>/', views.SoftwareRequestDetailView.as_view(), name='detail'),
]
