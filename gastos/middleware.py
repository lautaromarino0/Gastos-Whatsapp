"""
Middleware personalizado para el manejo de webhooks de Twilio
"""


class DisableCSRFMiddleware:
    """
    Desactiva la verificación CSRF para webhooks de Twilio
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Desactivar CSRF para las rutas de webhook
        if request.path.startswith('/webhook/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        response = self.get_response(request)
        return response
