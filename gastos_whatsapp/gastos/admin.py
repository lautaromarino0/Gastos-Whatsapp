from django.contrib import admin
from .models import Gasto


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['categoria', 'monto', 'telefono', 'fecha']
    list_filter = ['categoria', 'fecha', 'telefono']
    search_fields = ['categoria', 'telefono', 'mensaje_original']
    readonly_fields = ['fecha']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-fecha')
