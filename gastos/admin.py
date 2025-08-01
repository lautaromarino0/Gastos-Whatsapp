from django.contrib import admin
from .models import Gasto


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Gasto
    """
    list_display = ['categoria', 'monto', 'numero_telefono', 'fecha', 'fecha_str']
    list_filter = ['categoria', 'fecha', 'numero_telefono']
    search_fields = ['categoria', 'numero_telefono', 'mensaje_original']
    readonly_fields = ['fecha']
    ordering = ['-fecha']
    
    fieldsets = (
        ('Información del Gasto', {
            'fields': ('numero_telefono', 'categoria', 'monto')
        }),
        ('Metadatos', {
            'fields': ('fecha', 'mensaje_original'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimizar consultas
        """
        return super().get_queryset(request)
