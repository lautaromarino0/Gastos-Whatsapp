# Gastos WhatsApp - API Django + Twilio

Sistema para registrar gastos personales mediante mensajes de WhatsApp usando Django REST Framework y Twilio.

## 🚀 Características

- ✅ Registro de gastos vía WhatsApp con formato simple: "comida 200"
- ✅ Resúmenes de gastos por período: "resumen hoy", "resumen semana", "resumen 01-07 al 29-07"
- ✅ Validación por número de teléfono autorizado
- ✅ API REST para consultar gastos
- ✅ Panel de administración de Django
- ✅ Logging de actividades
- ✅ Preparado para integración con Celery (futuro)

## 📋 Prerequisitos

- Python 3.8+
- Cuenta de Twilio con WhatsApp Business API
- ngrok (para desarrollo local)

## 🛠️ Instalación

### 1. Clonar y configurar entorno

```bash
cd "c:\Users\Usuario\Desktop\Proyectos\Gastos Whatsapp"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

**⚠️ IMPORTANTE: Nunca subas el archivo .env a git**

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales reales de Twilio:

```env
# Django
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
DEBUG=True

# Twilio - Obtener de https://console.twilio.com/
TWILIO_ACCOUNT_SID=tu-account-sid-de-twilio
TWILIO_AUTH_TOKEN=tu-auth-token-de-twilio
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Números autorizados (separados por comas)
AUTHORIZED_PHONES=+549353123123,+5401122334455
```

### 3. Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Ejecutar servidor

```bash
python manage.py runserver 0.0.0.0:8000
```

## 🌐 Configuración de Twilio

### 1. Configurar Webhook URL

En tu consola de Twilio, configura el webhook de WhatsApp:

**Desarrollo local (con ngrok):**
```bash
ngrok http 8000
```
Usa la URL: `https://tu-url-ngrok.ngrok.io/webhook/whatsapp/`

**Producción:**
```
https://tu-dominio.com/webhook/whatsapp/
```

### 2. Formato de números

Los números deben estar en formato internacional:
- ✅ Correcto: `+540353123123`
- ❌ Incorrecto: `03534177510`

## 💬 Uso por WhatsApp

### Registrar gastos
```
comida 200
Netflix 1500
transporte 50.5
supermercado 2500
```

### Ver resúmenes
```
resumen hoy
resumen semana
resumen 01-07 al 29-07
```

### Respuestas del bot

**Gasto registrado:**
```
✅ Gasto registrado:
💰 Comida: $200
📅 01/08/2025 14:30
```

**Resumen:**
```
📊 Resumen 01/08 al 01/08:

💰 Total gastado: $2750
📝 Cantidad de gastos: 4

📂 Por categoría:
• Comida: $200
• Netflix: $1500
• Transporte: $50
• Supermercado: $2500
```

**Error de formato:**
```
❓ No entendí tu mensaje.

📝 Para registrar gastos:
• Comida 300
• Netflix 1500
• Transporte 50

📊 Para ver resúmenes:
• resumen hoy
• resumen semana
• resumen 01-07 al 29-07
```

## 🔧 API Endpoints

### Webhooks
- `POST /webhook/whatsapp/` - Recibe mensajes de Twilio

### API REST
- `GET /api/gastos/` - Lista todos los gastos
- `GET /api/gastos/{id}/` - Detalle de un gasto específico
- `GET /health/` - Health check del servicio

### Ejemplos de uso de la API

```bash
# Listar gastos
curl http://localhost:8000/api/gastos/

# Ver gasto específico
curl http://localhost:8000/api/gastos/1/

# Health check
curl http://localhost:8000/health/
```

## 🧪 Pruebas

### Probar procesamiento de mensajes

```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Probar registro de gasto
python manage.py test_message "+540353123123" "comida 300"

# Probar resumen
python manage.py test_message "+540353123123" "resumen hoy"

# Probar número no autorizado
python manage.py test_message "+5491122334455" "comida 100"
```

## 📊 Panel de Administración

Accede a `http://localhost:8000/admin/` para:

- Ver todos los gastos registrados
- Filtrar por categoría, fecha o teléfono
- Buscar gastos específicos
- Editar o eliminar registros

## 📁 Estructura del Proyecto

```
gastos_whatsapp/
├── gastos/
│   ├── management/
│   │   └── commands/
│   │       └── test_message.py
│   ├── migrations/
│   ├── admin.py              # Configuración del admin
│   ├── models.py             # Modelo Gasto
│   ├── serializers.py        # Serializers DRF
│   ├── services.py           # Lógica de negocio
│   ├── urls.py               # URLs de la app
│   ├── views.py              # Vistas de la API
│   └── middleware.py         # Middleware personalizado
├── gastos_whatsapp/
│   ├── settings.py           # Configuración Django
│   └── urls.py               # URLs principales
├── .env                      # Variables de entorno
├── requirements.txt          # Dependencias
└── manage.py
```

## 🔒 Seguridad

- ✅ Validación por números de teléfono autorizados
- ✅ Logging de todas las actividades (sin credenciales)
- ✅ Variables de entorno para datos sensibles
- ✅ Middleware para webhooks sin CSRF
- ⚠️ **NUNCA subas archivos .env o .log a git**
- ⚠️ **Regenera credenciales si se exponen accidentalmente**

### 🚨 En caso de exposición de credenciales:

1. Regenerar Auth Token en Twilio Console
2. Actualizar archivo `.env` local
3. Limpiar historial de git si es necesario
4. Verificar que `.gitignore` incluya archivos sensibles

## 🚀 Despliegue en Producción

### Variables de entorno importantes

```env
SECRET_KEY=clave-super-secreta-de-produccion
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
```

### Consideraciones adicionales

1. **Base de datos:** Cambiar a PostgreSQL o MySQL
2. **Archivos estáticos:** Configurar recolección de statics
3. **HTTPS:** Obligatorio para webhooks de Twilio
4. **Logs:** Configurar rotación de logs
5. **Monitoreo:** Implementar health checks

## 📝 Próximas Funcionalidades

- [ ] Integración con Celery para recordatorios automáticos
- [ ] Exportar gastos a CSV/Excel
- [ ] Gráficos de gastos por período
- [ ] Notificaciones de límites de gasto
- [ ] Categorías predefinidas
- [ ] Múltiples usuarios

## 🐛 Solución de Problemas

### Error: No se puede conectar a Twilio
- Verificar `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`
- Comprobar conectividad a internet

### No recibo mensajes
- Verificar webhook URL en Twilio
- Comprobar que el servidor esté accesible públicamente
- Revisar logs: `tail -f gastos_whatsapp.log`

### Número no autorizado
- Verificar formato del número en `.env`
- Usar formato internacional: `+540353123123`

## 📞 Soporte

Para problemas o sugerencias, revisar los logs en `gastos_whatsapp.log` o contactar al desarrollador.
