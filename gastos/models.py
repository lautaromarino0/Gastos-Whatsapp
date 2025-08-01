from django.db import models
from django.utils import timezone


class Gasto(models.Model):
    """
    Modelo para registrar gastos personales recibidos vía WhatsApp
    """
    numero_telefono = models.CharField(
        max_length=20,
        help_text="Número de teléfono del usuario (ej: +5403535123123)"
    )
    categoria = models.CharField(
        max_length=100,
        help_text="Categoría del gasto (ej: comida, transporte, Netflix)"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto del gasto"
    )
    fecha = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora del registro del gasto"
    )
    mensaje_original = models.TextField(
        help_text="Mensaje original recibido por WhatsApp"
    )
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
    
    def __str__(self):
        return f"{self.categoria}: ${self.monto} - {self.fecha.strftime('%d/%m/%Y')}"
    
    @property
    def fecha_str(self):
        """Retorna la fecha en formato legible"""
        return self.fecha.strftime('%d/%m/%Y %H:%M')
