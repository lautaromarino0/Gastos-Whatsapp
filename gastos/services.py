"""
Servicios para procesar mensajes de WhatsApp y gestionar gastos
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from twilio.rest import Client
import logging

from .models import Gasto

logger = logging.getLogger('gastos')


class WhatsAppService:
    """
    Servicio para gestionar mensajes de WhatsApp via Twilio
    """
    
    def __init__(self):
        try:
            # Verificar que las credenciales estén configuradas
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.error("Credenciales de Twilio no configuradas")
                self.client = None
            else:
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("Cliente de Twilio inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando cliente de Twilio: {str(e)}")
            self.client = None
    
    def send_message(self, to_number, message):
        """
        Envía un mensaje de WhatsApp
        """
        if not self.client:
            logger.error("Cliente de Twilio no disponible")
            return False
            
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{to_number}'
            )
            logger.info(f"Mensaje enviado a {to_number}: {message_obj.sid}")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje a {to_number}: {str(e)}")
            return False


class GastoService:
    """
    Servicio para procesar y gestionar gastos
    """
    
    @staticmethod
    def is_authorized_phone(phone_number):
        """
        Verifica si el número de teléfono está autorizado
        """
        # Limpiar el número (remover espacios, guiones, etc.)
        clean_phone = re.sub(r'[^\d+]', '', phone_number)
        authorized_phones = [re.sub(r'[^\d+]', '', phone) for phone in settings.AUTHORIZED_PHONES]
        
        return clean_phone in authorized_phones
    
    @staticmethod
    def parse_gasto_message(message):
        """
        Parsea un mensaje para extraer categoría y monto
        Formatos soportados:
        - "comida 200"
        - "Netflix 1500"
        - "transporte 50.5"
        """
        # Limpiar el mensaje
        message = message.strip().lower()
        
        # Patrón: palabra(s) seguida de número (entero o decimal)
        pattern = r'^(.+?)\s+(\d+(?:\.\d+)?)$'
        match = re.match(pattern, message)
        
        if match:
            categoria = match.group(1).strip().title()
            try:
                monto = Decimal(match.group(2))
                return categoria, monto
            except InvalidOperation:
                return None, None
        
        return None, None
    
    @staticmethod
    def create_gasto(phone_number, categoria, monto, original_message):
        """
        Crea un nuevo gasto
        """
        try:
            gasto = Gasto.objects.create(
                numero_telefono=phone_number,
                categoria=categoria,
                monto=monto,
                mensaje_original=original_message
            )
            logger.info(f"Gasto creado: {gasto}")
            return gasto
        except Exception as e:
            logger.error(f"Error creando gasto: {str(e)}")
            return None
    
    @staticmethod
    def delete_gasto(phone_number, gasto_id):
        """
        Elimina un gasto específico
        """
        try:
            gasto = Gasto.objects.get(id=gasto_id, numero_telefono=phone_number)
            gasto_info = f"{gasto.categoria}: ${gasto.monto}"
            gasto.delete()
            logger.info(f"Gasto eliminado: ID {gasto_id}")
            return gasto_info
        except Gasto.DoesNotExist:
            logger.error(f"Gasto no encontrado: ID {gasto_id}")
            return None
        except Exception as e:
            logger.error(f"Error eliminando gasto: {str(e)}")
            return None
    
    @staticmethod
    def delete_last_gasto(phone_number):
        """
        Elimina el último gasto del usuario
        """
        try:
            gasto = Gasto.objects.filter(numero_telefono=phone_number).order_by('-fecha').first()
            if gasto:
                gasto_info = f"{gasto.categoria}: ${gasto.monto}"
                gasto.delete()
                logger.info(f"Ultimo gasto eliminado: {gasto_info}")
                return gasto_info
            else:
                return None
        except Exception as e:
            logger.error(f"Error eliminando ultimo gasto: {str(e)}")
            return None
    
    @staticmethod
    def get_recent_gastos(phone_number, limit=5):
        """
        Obtiene los gastos más recientes del usuario
        """
        try:
            gastos = Gasto.objects.filter(numero_telefono=phone_number).order_by('-fecha')[:limit]
            return list(gastos)
        except Exception as e:
            logger.error(f"Error obteniendo gastos recientes: {str(e)}")
            return []
    
    @staticmethod
    def parse_delete_message(message):
        """
        Parsea mensajes de eliminación
        Formatos soportados:
        - "eliminar 3"
        - "eliminar ultimo"
        - "borrar 5"
        - "borrar ultimo"
        """
        message = message.strip().lower()
        
        # Patrón para eliminar por ID
        pattern_id = r'^(eliminar|borrar)\s+(\d+)$'
        match_id = re.match(pattern_id, message)
        
        if match_id:
            try:
                gasto_id = int(match_id.group(2))
                return 'id', gasto_id
            except ValueError:
                return None, None
        
        # Patrón para eliminar último
        pattern_last = r'^(eliminar|borrar)\s+(ultimo|último)$'
        match_last = re.match(pattern_last, message)
        
        if match_last:
            return 'ultimo', None
        
        return None, None
    
    @staticmethod
    def parse_resumen_message(message):
        """
        Parsea mensajes de resumen
        Formatos soportados:
        - "resumen hoy"
        - "resumen semana"
        - "resumen 01-07 al 29-07"
        """
        message = message.strip().lower()
        
        if message == "resumen hoy":
            today = timezone.now().date()
            return today, today
        
        elif message == "resumen semana":
            today = timezone.now().date()
            start_week = today - timedelta(days=today.weekday())
            return start_week, today
        
        elif message.startswith("resumen "):
            # Patrón para "resumen DD-MM al DD-MM"
            pattern = r'resumen\s+(\d{1,2}-\d{1,2})\s+al\s+(\d{1,2}-\d{1,2})'
            match = re.match(pattern, message)
            
            if match:
                try:
                    start_str = match.group(1)
                    end_str = match.group(2)
                    
                    # Asumir año actual
                    current_year = timezone.now().year
                    
                    # Parsear fechas
                    start_day, start_month = map(int, start_str.split('-'))
                    end_day, end_month = map(int, end_str.split('-'))
                    
                    start_date = datetime(current_year, start_month, start_day).date()
                    end_date = datetime(current_year, end_month, end_day).date()
                    
                    return start_date, end_date
                except (ValueError, IndexError):
                    return None, None
        
        return None, None
    
    @staticmethod
    def get_resumen_gastos(phone_number, start_date, end_date):
        """
        Obtiene un resumen de gastos para un período
        """
        # Convertir fechas a datetime para la consulta
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        # Filtrar gastos
        gastos = Gasto.objects.filter(
            numero_telefono=phone_number,
            fecha__range=[start_datetime, end_datetime]
        )
        
        # Calcular total
        total = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        # Agrupar por categoría
        gastos_por_categoria = {}
        for gasto in gastos:
            categoria = gasto.categoria
            if categoria in gastos_por_categoria:
                gastos_por_categoria[categoria] += gasto.monto
            else:
                gastos_por_categoria[categoria] = gasto.monto
        
        return {
            'total_gastado': total,
            'gastos_por_categoria': gastos_por_categoria,
            'cantidad_gastos': gastos.count(),
            'periodo': f"{start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}"
        }


class MessageProcessor:
    """
    Procesador principal de mensajes de WhatsApp
    """
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    def process_message(self, phone_number, message_body):
        """
        Procesa un mensaje entrante y retorna la respuesta
        """
        # Verificar autorización
        if not GastoService.is_authorized_phone(phone_number):
            return "No estas autorizado para usar este servicio."
        
        message_body = message_body.strip()
        
        # Verificar si es un mensaje de resumen
        if message_body.lower().startswith('resumen'):
            return self._process_resumen_message(phone_number, message_body)
        
        # Verificar si es un mensaje de eliminación
        if message_body.lower().startswith(('eliminar', 'borrar')):
            return self._process_delete_message(phone_number, message_body)
        
        # Verificar si quiere ver sus gastos recientes
        if message_body.lower() in ['mis gastos', 'gastos', 'ver gastos']:
            return self._process_list_gastos_message(phone_number)
        
        # Intentar parsear como gasto
        categoria, monto = GastoService.parse_gasto_message(message_body)
        
        if categoria and monto:
            return self._process_gasto_message(phone_number, categoria, monto, message_body)
        
        # Mensaje no entendido
        return self._get_help_message()
    
    def _process_gasto_message(self, phone_number, categoria, monto, original_message):
        """
        Procesa un mensaje de gasto
        """
        gasto = GastoService.create_gasto(phone_number, categoria, monto, original_message)
        
        if gasto:
            return f"Gasto registrado: {categoria}: ${monto} - {gasto.fecha_str}"
        else:
            return "Error al registrar el gasto. Intenta nuevamente."
    
    def _process_resumen_message(self, phone_number, message):
        """
        Procesa un mensaje de resumen
        """
        start_date, end_date = GastoService.parse_resumen_message(message)
        
        if not start_date or not end_date:
            return "Formato de resumen no valido. Usa: 'resumen hoy', 'resumen semana' o 'resumen 01-07 al 29-07'"
        
        resumen = GastoService.get_resumen_gastos(phone_number, start_date, end_date)
        
        # Formatear respuesta
        if resumen['cantidad_gastos'] == 0:
            return f"Sin gastos registrados para el periodo {resumen['periodo']}"
        
        response = f"Resumen {resumen['periodo']}:\n\n"
        response += f"Total gastado: ${resumen['total_gastado']}\n"
        response += f"Cantidad de gastos: {resumen['cantidad_gastos']}\n\n"
        response += "Por categoria:\n"
        
        for categoria, monto in resumen['gastos_por_categoria'].items():
            response += f"- {categoria}: ${monto}\n"
        
        return response
    
    def _process_delete_message(self, phone_number, message):
        """
        Procesa un mensaje de eliminación de gasto
        """
        delete_type, gasto_id = GastoService.parse_delete_message(message)
        
        if not delete_type:
            return "Formato incorrecto. Usa: 'eliminar 3' o 'eliminar ultimo'"
        
        if delete_type == 'id':
            gasto_info = GastoService.delete_gasto(phone_number, gasto_id)
            if gasto_info:
                return f"Gasto eliminado: {gasto_info}"
            else:
                return f"No se encontro el gasto con ID {gasto_id}"
        
        elif delete_type == 'ultimo':
            gasto_info = GastoService.delete_last_gasto(phone_number)
            if gasto_info:
                return f"Ultimo gasto eliminado: {gasto_info}"
            else:
                return "No tienes gastos para eliminar"
        
        return "Error al eliminar el gasto"
    
    def _process_list_gastos_message(self, phone_number):
        """
        Procesa un mensaje para mostrar gastos recientes
        """
        gastos = GastoService.get_recent_gastos(phone_number, 5)
        
        if not gastos:
            return "No tienes gastos registrados"
        
        response = "Tus ultimos gastos:\n\n"
        for gasto in gastos:
            response += f"ID {gasto.id}: {gasto.categoria} - ${gasto.monto}\n"
            response += f"   Fecha: {gasto.fecha.strftime('%d/%m %H:%M')}\n\n"
        
        response += "Para eliminar: 'eliminar 3' o 'eliminar ultimo'"
        return response
    
    def _get_help_message(self):
        """
        Retorna el mensaje de ayuda
        """
        return (
            "No entendi tu mensaje.\n\n"
            "Para registrar gastos:\n"
            "- Comida 300\n"
            "- Netflix 1500\n"
            "- Transporte 50\n\n"
            "Para ver resumenes:\n"
            "- resumen hoy\n"
            "- resumen semana\n"
            "- resumen 01-07 al 29-07\n\n"
            "Para gestionar gastos:\n"
            "- mis gastos\n"
            "- eliminar 3\n"
            "- eliminar ultimo"
        )
    
    def send_response(self, phone_number, message):
        """
        Envía una respuesta por WhatsApp
        """
        return self.whatsapp_service.send_message(phone_number, message)
