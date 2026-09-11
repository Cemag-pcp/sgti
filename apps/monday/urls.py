from django.urls import path

from . import views

app_name = 'monday'

urlpatterns = [
    path('planos-de-acao/', views.ActionPlansView.as_view(), name='action_plans'),
    path('planos-de-acao/dados/', views.ActionPlansDataView.as_view(), name='action_plans_data'),
    path('subelemento/<str:subitem_id>/converter/', views.ConvertSubitemToTicketView.as_view(), name='convert_subitem'),
]
