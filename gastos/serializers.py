from rest_framework import serializers
from .models import Gasto


class GastoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Gasto
    """
    fecha_str = serializers.ReadOnlyField()
    
    class Meta:
        model = Gasto
        fields = ['id', 'numero_telefono', 'categoria', 'monto', 'fecha', 'fecha_str', 'mensaje_original']
        read_only_fields = ['id', 'fecha']


class ResumenGastosSerializer(serializers.Serializer):
    """
    Serializer para el resumen de gastos
    """
    total_gastado = serializers.DecimalField(max_digits=10, decimal_places=2)
    periodo = serializers.CharField()
    gastos_por_categoria = serializers.DictField()
    cantidad_gastos = serializers.IntegerField()
