from django.db import models
from django.utils import timezone
from decimal import Decimal


class Gasto(models.Model):
    telefono = models.CharField(
        max_length=20,
        help_text="Número de teléfono del usuario (formato: +5491123456789)"
    )
    categoria = models.CharField(
        max_length=100,
        help_text="Categoría del gasto (ej: comida, transporte, entretenimiento)"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto del gasto"
    )
    fecha = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora del gasto"
    )
    mensaje_original = models.TextField(
        blank=True,
        help_text="Mensaje original de WhatsApp"
    )
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
    
    def __str__(self):
        return f"{self.categoria}: ${self.monto} - {self.fecha.strftime('%d/%m/%Y')}"
    
    @classmethod
    def resumen_por_categoria(cls, telefono, fecha_inicio=None, fecha_fin=None):
        """
        Devuelve un resumen de gastos agrupados por categoría
        """
        queryset = cls.objects.filter(telefono=telefono)
        
        if fecha_inicio:
            queryset = queryset.filter(fecha__date__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__date__lte=fecha_fin)
        
        # Agrupar por categoría y sumar montos
        from django.db.models import Sum
        resumen = queryset.values('categoria').annotate(
            total=Sum('monto')
        ).order_by('-total')
        
        total_general = queryset.aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
        
        return {
            'total_general': total_general,
            'por_categoria': list(resumen),
            'cantidad_gastos': queryset.count()
        }
