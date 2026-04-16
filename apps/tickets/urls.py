from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('api/devices/', views.DeviceListApiView.as_view(), name='api_devices'),
    path('api/last-ticket/', views.LastTicketByMatriculaApiView.as_view(), name='api_last_ticket'),
    path('api/push/subscription/', views.PushSubscriptionView.as_view(), name='push_subscription'),
    path('api/open/', views.TicketCreateApiView.as_view(), name='api_open'),
    path('api/notifications/poll/', views.TicketNotificationsPollView.as_view(), name='notifications_poll'),
    path('webhooks/whatsapp/', views.WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('', views.TicketListView.as_view(), name='list'),
    path('reports/', views.TicketReportsView.as_view(), name='reports'),
    path('submit/', views.TicketSubmitView.as_view(), name='submit'),
    path('submit/requester-lookup/', views.RequesterLookupView.as_view(), name='requester_lookup'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TicketUpdateView.as_view(), name='edit'),
    path('<int:pk>/assign/', views.TicketAssignView.as_view(), name='assign'),
    path('<int:pk>/status/', views.TicketStatusView.as_view(), name='status'),
    path('<int:pk>/time-entries/add/', views.TimeEntryCreateView.as_view(), name='time_entry_add'),
    path('<int:pk>/observations/add/', views.ObservationCreateView.as_view(), name='observation_add'),
    path('config/sla/', views.SLAConfigView.as_view(), name='sla_config'),
    path('config/locations/', views.LocationListView.as_view(), name='location_list'),
    path('config/locations/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('config/locations/<int:pk>/edit/', views.LocationUpdateView.as_view(), name='location_edit'),
    path('config/locations/<int:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    path('config/devices/', views.DeviceListView.as_view(), name='device_list'),
    path('config/devices/create/', views.DeviceCreateView.as_view(), name='device_create'),
    path('config/devices/<int:pk>/edit/', views.DeviceUpdateView.as_view(), name='device_edit'),
    path('config/devices/<int:pk>/delete/', views.DeviceDeleteView.as_view(), name='device_delete'),
]
