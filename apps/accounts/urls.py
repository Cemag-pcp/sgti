from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    path('requesters/', views.RequesterListView.as_view(), name='requester_list'),
    path('requesters/create/', views.RequesterCreateView.as_view(), name='requester_create'),
    path('requesters/<int:pk>/edit/', views.RequesterUpdateView.as_view(), name='requester_edit'),
    path('requesters/<int:pk>/delete/', views.RequesterDeleteView.as_view(), name='requester_delete'),
]
