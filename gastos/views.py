from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .services import MessageProcessor
from .models import Gasto
from .serializers import GastoSerializer, ResumenGastosSerializer

logger = logging.getLogger('gastos')


@method_decorator(csrf_exempt, name='dispatch')
class TwilioWebhookView(APIView):
    """
    Vista para recibir webhooks de Twilio WhatsApp
    """
    
    def post(self, request):
        """
        Procesa mensajes entrantes de WhatsApp
        """
        try:
            # Log de debugging
            logger.info("=== WEBHOOK RECIBIDO ===")
            logger.info(f"Método: {request.method}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"POST data: {dict(request.POST)}")
            
            # Obtener datos del webhook (Twilio envía como form data)
            from_number = request.POST.get('From', '').replace('whatsapp:', '')
            message_body = request.POST.get('Body', '')
            
            logger.info(f"Número origen: {from_number}")
            logger.info(f"Mensaje: {message_body}")
            
            if not from_number or not message_body:
                logger.error("Datos del webhook incompletos")
                return Response({'status': 'error', 'message': 'Datos incompletos'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Procesar mensaje
            processor = MessageProcessor()
            response_message = processor.process_message(from_number, message_body)
            
            logger.info(f"Respuesta generada: {response_message}")
            
            # Enviar respuesta
            success = processor.send_response(from_number, response_message)
            
            if success:
                logger.info(f"Respuesta enviada correctamente")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                logger.error(f"Error enviando respuesta")
                return Response({'status': 'warning', 'message': 'Procesado pero no enviado'}, 
                              status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'status': 'error', 'message': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GastoListView(APIView):
    """
    Vista para listar gastos
    """
    
    def get(self, request):
        """
        Lista todos los gastos
        """
        gastos = Gasto.objects.all()
        serializer = GastoSerializer(gastos, many=True)
        return Response(serializer.data)


class GastoDetailView(APIView):
    """
    Vista para ver detalle de un gasto
    """
    
    def get(self, request, pk):
        """
        Obtiene un gasto específico
        """
        try:
            gasto = Gasto.objects.get(pk=pk)
            serializer = GastoSerializer(gasto)
            return Response(serializer.data)
        except Gasto.DoesNotExist:
            return Response({'error': 'Gasto no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class HealthCheckView(APIView):
    """
    Vista para verificar el estado del servicio
    """
    
    def get(self, request):
        """
        Endpoint de health check
        """
        return Response({
            'status': 'healthy',
            'service': 'Gastos WhatsApp API',
            'version': '1.0.0'
        })
