from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from twilio.twiml.messaging_response import MessagingResponse
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
from decouple import config

from .models import Gasto


class WhatsAppWebhookView(APIView):
    """
    API que recibe los mensajes de WhatsApp vía Twilio Webhook
    """
    
    def post(self, request):
        # Obtener datos del webhook de Twilio
        from_number = request.data.get('From', '').replace('whatsapp:', '')
        message_body = request.data.get('Body', '').strip()
        
        # Validar número autorizado
        authorized_phones = config('AUTHORIZED_PHONES', default='').split(',')
        if from_number not in authorized_phones:
            return self._send_response("❌ Número no autorizado.")
        
        # Procesar el mensaje
        response_message = self._process_message(from_number, message_body)
        
        # Crear respuesta de Twilio
        return self._send_response(response_message)
    
    def _process_message(self, telefono, mensaje):
        """
        Procesa el mensaje recibido y determina la acción a realizar
        """
        mensaje_lower = mensaje.lower().strip()
        
        # Comando de resumen
        if mensaje_lower.startswith('resumen'):
            return self._handle_resumen(telefono, mensaje_lower)
        
        # Comando de ayuda
        if mensaje_lower in ['ayuda', 'help', '?']:
            return self._get_help_message()
        
        # Intentar parsear como gasto
        gasto_data = self._parse_gasto(mensaje)
        if gasto_data:
            return self._save_gasto(telefono, mensaje, gasto_data)
        
        # Mensaje no entendido
        return self._get_help_message()
    
    def _parse_gasto(self, mensaje):
        """
        Intenta parsear un mensaje como gasto
        Formatos válidos: "comida 200", "Netflix 1500", "transporte 50.5"
        """
        # Patrón: palabra(s) + número (con posible decimal)
        pattern = r'^(.+?)\s+(\d+(?:\.\d{1,2})?)$'
        match = re.match(pattern, mensaje.strip())
        
        if match:
            categoria = match.group(1).strip().lower()
            try:
                monto = Decimal(match.group(2))
                return {'categoria': categoria, 'monto': monto}
            except InvalidOperation:
                return None
        
        return None
    
    def _save_gasto(self, telefono, mensaje_original, gasto_data):
        """
        Guarda un nuevo gasto en la base de datos
        """
        try:
            gasto = Gasto.objects.create(
                telefono=telefono,
                categoria=gasto_data['categoria'],
                monto=gasto_data['monto'],
                mensaje_original=mensaje_original
            )
            
            return f"✅ Gasto registrado:\n💰 {gasto.categoria.title()}: ${gasto.monto}\n📅 {gasto.fecha.strftime('%d/%m/%Y %H:%M')}"
            
        except Exception as e:
            return f"❌ Error al guardar el gasto: {str(e)}"
    
    def _handle_resumen(self, telefono, mensaje):
        """
        Maneja los comandos de resumen
        """
        if 'hoy' in mensaje:
            return self._resumen_hoy(telefono)
        elif 'semana' in mensaje:
            return self._resumen_semana(telefono)
        else:
            # Intentar parsear rango de fechas
            fecha_match = re.search(r'(\d{2}-\d{2})\s+al?\s+(\d{2}-\d{2})', mensaje)
            if fecha_match:
                return self._resumen_rango(telefono, fecha_match.group(1), fecha_match.group(2))
            else:
                return "❌ Formato de fecha no válido. Usa: 'resumen 01-07 al 29-07'"
    
    def _resumen_hoy(self, telefono):
        """
        Resumen de gastos del día actual
        """
        hoy = timezone.now().date()
        resumen = Gasto.resumen_por_categoria(telefono, hoy, hoy)
        
        return self._format_resumen(resumen, f"📊 Resumen de hoy ({hoy.strftime('%d/%m/%Y')})")
    
    def _resumen_semana(self, telefono):
        """
        Resumen de gastos de la semana actual
        """
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        resumen = Gasto.resumen_por_categoria(telefono, inicio_semana, hoy)
        
        return self._format_resumen(
            resumen, 
            f"📊 Resumen de la semana ({inicio_semana.strftime('%d/%m')} al {hoy.strftime('%d/%m')})"
        )
    
    def _resumen_rango(self, telefono, fecha_inicio_str, fecha_fin_str):
        """
        Resumen de gastos en un rango de fechas
        """
        try:
            # Parsear fechas (formato DD-MM)
            año_actual = timezone.now().year
            
            dia_ini, mes_ini = map(int, fecha_inicio_str.split('-'))
            dia_fin, mes_fin = map(int, fecha_fin_str.split('-'))
            
            fecha_inicio = datetime(año_actual, mes_ini, dia_ini).date()
            fecha_fin = datetime(año_actual, mes_fin, dia_fin).date()
            
            resumen = Gasto.resumen_por_categoria(telefono, fecha_inicio, fecha_fin)
            
            return self._format_resumen(
                resumen,
                f"📊 Resumen del {fecha_inicio.strftime('%d/%m')} al {fecha_fin.strftime('%d/%m')}"
            )
            
        except ValueError:
            return "❌ Formato de fecha inválido. Usa DD-MM (ej: 01-07 al 29-07)"
    
    def _format_resumen(self, resumen, titulo):
        """
        Formatea el resumen para mostrar en WhatsApp
        """
        if resumen['cantidad_gastos'] == 0:
            return f"{titulo}\n\n🤷‍♂️ No hay gastos registrados en este período."
        
        mensaje = f"{titulo}\n\n"
        mensaje += f"💰 Total: ${resumen['total_general']}\n"
        mensaje += f"📝 Gastos registrados: {resumen['cantidad_gastos']}\n\n"
        mensaje += "📋 Por categoría:\n"
        
        for categoria in resumen['por_categoria']:
            mensaje += f"• {categoria['categoria'].title()}: ${categoria['total']}\n"
        
        return mensaje
    
    def _get_help_message(self):
        """
        Mensaje de ayuda cuando no se entiende el comando
        """
        return (
            "🤖 *Asistente de Gastos*\n\n"
            "📝 Para registrar un gasto:\n"
            "• Comida 300\n"
            "• Netflix 1500\n"
            "• Transporte 50.5\n\n"
            "📊 Para ver resúmenes:\n"
            "• resumen hoy\n"
            "• resumen semana\n"
            "• resumen 01-07 al 29-07\n\n"
            "❓ Escribe 'ayuda' para ver este mensaje."
        )
    
    def _send_response(self, message):
        """
        Envía la respuesta usando TwiML
        """
        response = MessagingResponse()
        response.message(message)
        
        return HttpResponse(str(response), content_type='text/xml')
