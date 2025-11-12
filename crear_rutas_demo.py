import os
import django
from datetime import datetime, timedelta
import uuid

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corredor.settings')  # ⚠️ Cambia 'tu_proyecto' por el nombre real
django.setup()

from transporte.models import Empresa, Chofer, Vehiculo, Carga, ViajeDemo, PosicionDemo
from django.utils import timezone

# -------------------------------
# DATOS BASE
# -------------------------------
EMPRESA_NOMBRE = "DemoTrans"
CHOFER_NOMBRE = "Juan Pérez"
VEHICULO_PATENTE = "AB123CD"
CARGA_TIPO = "Minerales"

# -------------------------------
# LOCALIDADES JUJEÑAS
# -------------------------------
localidades = [
    ("San Salvador de Jujuy", -24.1858, -65.2995),
    ("Palpalá", -24.2569, -65.2081),
    ("Perico", -24.3840, -65.1124),
    ("El Carmen", -24.3907, -65.2610),
    ("San Pedro de Jujuy", -24.2333, -64.8667),
    ("Libertador Gral. San Martín", -23.8067, -64.7873),
    ("Calilegua", -23.7781, -64.7703),
    ("Fraile Pintado", -23.9469, -64.7931),
    ("La Mendieta", -24.2833, -64.8667),
    ("Tilcara", -23.5773, -65.3935),
    ("Humahuaca", -23.2057, -65.3504),
]

# -------------------------------
# CREAR EMPRESA / CHOFER / VEHÍCULO / CARGA
# -------------------------------
empresa, _ = Empresa.objects.get_or_create(nombre=EMPRESA_NOMBRE, defaults={
    "cuit": "30-99999999-9",
    "direccion": "Av. Principal 123",
    "contacto": "contacto@demotrans.com",
    "usuario_id": 1  # ⚠️ Asegúrate que exista un usuario con ID=1
})

chofer, _ = Chofer.objects.get_or_create(empresa=empresa, documento="99999999", defaults={
    "nombre": "Juan",
    "apellido": "Pérez",
    "licencia_nro": "JUJ-2025-001"
})

vehiculo, _ = Vehiculo.objects.get_or_create(empresa=empresa, patente=VEHICULO_PATENTE, defaults={
    "marca": "Iveco",
    "modelo": "Stralis",
    "capacidad": 20.0
})

carga, _ = Carga.objects.get_or_create(empresa=empresa, tipo=CARGA_TIPO, defaults={
    "peso_aprox": 15.0,
    "descripcion": "Carga de prueba - Minerales"
})

# -------------------------------
# CREAR VIAJES DEMO
# -------------------------------
ViajeDemo.objects.all().delete()
PosicionDemo.objects.all().delete()

print("Creando viajes demo...\n")

viajes_creados = 0
for i in range(10):
    origen, lat1, lon1 = localidades[i % len(localidades)]
    destino, lat2, lon2 = localidades[(i + 1) % len(localidades)]

    viaje_demo = ViajeDemo.objects.create(
        id=uuid.uuid4(),
        origen=origen,
        destino=destino,
        fecha_salida=timezone.now(),
        fecha_llegada_estimada=timezone.now() + timedelta(hours=2),
        empresa=empresa,
        chofer=chofer,
        vehiculo=vehiculo,
        carga=carga,
        estado="PROGRAMADO"
    )

    # Crear posiciones simuladas (inicio y fin)
    PosicionDemo.objects.create(viaje=viaje_demo, latitud=lat1, longitud=lon1)
    PosicionDemo.objects.create(viaje=viaje_demo, latitud=lat2, longitud=lon2)

    print(f" → Viaje demo {viaje_demo.origen} → {viaje_demo.destino}")
    viajes_creados += 1

print(f"\n✅ {viajes_creados} viajes demo creados correctamente.")
