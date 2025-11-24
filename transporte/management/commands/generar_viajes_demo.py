import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from geopy.distance import geodesic

from transporte.models import (
    Viaje,
    Empresa,
    Chofer,
    Vehiculo,
    Carga,
    PosicionGPS,
    calcular_metricas_viaje
)


# Coordenadas aproximadas de Jujuy para generar viajes realistas
PUNTOS = [
    (-24.1858, -65.2995),  # San Salvador de Jujuy
    (-24.2333, -65.2667),  # Reyes
    (-24.3833, -65.3000),  # El Carmen
    (-24.4333, -65.1500),  # Palpalá
    (-24.2667, -65.3167),  # Yala
    (-24.1167, -65.2833),  # Lozano
    (-23.9833, -65.3000),  # León
    (-24.5667, -65.3833),  # Perico
    (-23.7333, -65.5000),  # Tilcara
    (-22.1167, -65.3167),  # La Quiaca
]


class Command(BaseCommand):
    help = "Genera 20 viajes simulados completos"

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.WARNING("Generando viajes demo..."))

        empresas = list(Empresa.objects.all())
        choferes = list(Chofer.objects.all())
        vehiculos = list(Vehiculo.objects.all())
        cargas = list(Carga.objects.all())

        if not empresas or not choferes or not vehiculos or not cargas:
            self.stdout.write(self.style.ERROR("Debe haber empresa, choferes, vehículos y cargas en el sistema."))
            return

        for i in range(20):

            # Elegir puntos aleatorios
            origen = random.choice(PUNTOS)
            destino = random.choice(PUNTOS)
            while destino == origen:
                destino = random.choice(PUNTOS)

            empresa = random.choice(empresas)
            chofer = random.choice(choferes)
            vehiculo = random.choice(vehiculos)
            carga = random.choice(cargas)

            salida = make_aware(datetime.now() - timedelta(days=random.randint(1, 20)))
            llegada = salida + timedelta(hours=random.randint(1, 10))

            viaje = Viaje.objects.create(
                empresa=empresa,
                chofer=chofer,
                vehiculo=vehiculo,
                carga=carga,
                origen="Punto " + str(PUNTOS.index(origen)),
                destino="Punto " + str(PUNTOS.index(destino)),
                lat_origen=origen[0],
                lon_origen=origen[1],
                lat_destino=destino[0],
                lon_destino=destino[1],
                fecha_salida=salida,
                fecha_llegada_estimada=llegada,
                fecha_llegada_real=llegada,
                estado="FINALIZADO"
            )

            # Generar posiciones GPS simuladas
            total_puntos = random.randint(10, 25)
            lat_step = (destino[0] - origen[0]) / total_puntos
            lon_step = (destino[1] - origen[1]) / total_puntos

            for n in range(total_puntos):
                PosicionGPS.objects.create(
                    viaje=viaje,
                    latitud=origen[0] + (lat_step * n),
                    longitud=origen[1] + (lon_step * n)
                )

            # Calcular métricas reales
            calcular_metricas_viaje(viaje)

        self.stdout.write(self.style.SUCCESS("¡20 viajes simulados generados con éxito!"))
