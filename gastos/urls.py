from django.urls import path
from .views import TwilioWebhookView, GastoListView, GastoDetailView, HealthCheckView

app_name = 'gastos'

urlpatterns = [
    # Webhook de Twilio
    path('webhook/whatsapp/', TwilioWebhookView.as_view(), name='twilio-webhook'),
    
    # API endpoints
    path('api/gastos/', GastoListView.as_view(), name='gasto-list'),
    path('api/gastos/<int:pk>/', GastoDetailView.as_view(), name='gasto-detail'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
