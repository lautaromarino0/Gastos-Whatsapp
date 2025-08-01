from django.core.management.base import BaseCommand
from gastos.services import MessageProcessor


class Command(BaseCommand):
    """
    Comando para probar el procesamiento de mensajes
    """
    help = 'Prueba el procesamiento de mensajes de WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Número de teléfono')
        parser.add_argument('message', type=str, help='Mensaje a procesar')

    def handle(self, *args, **options):
        phone = options['phone']
        message = options['message']
        
        processor = MessageProcessor()
        response = processor.process_message(phone, message)
        
        self.stdout.write(f"📱 Número: {phone}")
        self.stdout.write(f"💬 Mensaje: {message}")
        self.stdout.write(f"🤖 Respuesta: {response}")
        self.stdout.write(self.style.SUCCESS('✅ Procesamiento completado'))
