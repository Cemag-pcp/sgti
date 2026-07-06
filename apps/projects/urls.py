from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('novo/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ProjectUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.ProjectStatusUpdateView.as_view(), name='status_update'),
    path('<int:pk>/excluir/', views.ProjectDeleteView.as_view(), name='delete'),
    path('<int:pk>/tarefas/nova/', views.ProjectTaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/tarefas/<int:task_pk>/editar/', views.ProjectTaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/tarefas/<int:task_pk>/status/', views.ProjectTaskStatusView.as_view(), name='task_status'),
    path('<int:pk>/tarefas/<int:task_pk>/excluir/', views.ProjectTaskDeleteView.as_view(), name='task_delete'),
    path('<int:pk>/membros/adicionar/', views.ProjectMemberAddView.as_view(), name='member_add'),
    path('<int:pk>/membros/<int:member_pk>/remover/', views.ProjectMemberRemoveView.as_view(), name='member_remove'),
    path('<int:pk>/atualizacoes/nova/', views.ProjectUpdateCreateView.as_view(), name='update_create'),
    path('<int:pk>/atualizacoes/<int:update_pk>/excluir/', views.ProjectUpdateDeleteView.as_view(), name='update_delete'),
]
