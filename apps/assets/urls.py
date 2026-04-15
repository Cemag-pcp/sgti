from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.AssetListView.as_view(), name='list'),
    path('create/', views.AssetCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AssetDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AssetUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.AssetDeleteView.as_view(), name='delete'),
    path('<int:pk>/assign/', views.AssetAssignView.as_view(), name='assign'),
    path('<int:pk>/maintenance/', views.AssetMaintenanceCreateView.as_view(), name='maintenance'),
]
