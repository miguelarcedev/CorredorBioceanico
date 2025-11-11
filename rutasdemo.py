import os
import django

# Ajusta aquí el nombre de tu proyecto Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corredor.settings')
django.setup()

from transporte.models import ViajeDemo, RutaDemo

# Lista de viajes demo con descripción y conjunto de coordenadas (simplificadas)
viajes_info = [
    {
        "nombre": "San Salvador → Perico",
        "coords": [
            (-24.1858, -65.2995),
            (-24.2000, -65.2850),
            (-24.2500, -65.2500),
            (-24.3000, -65.2000),
            (-24.3825, -65.0415),
        ],
    },
    {
        "nombre": "San Salvador → Yala",
        "coords": [
            (-24.1858, -65.2995),
            (-24.1500, -65.3100),
            (-24.1000, -65.3200),
            (-24.0550, -65.3330),
        ],
    },
    {
        "nombre": "San Salvador → Palpalá",
        "coords": [
            (-24.1858, -65.2995),
            (-24.2300, -65.2600),
            (-24.2600, -65.2400),
            (-24.2900, -65.2200),
            (-24.3100, -65.2000),
        ],
    },
    {
        "nombre": "San Salvador → Tilcara",
        "coords": [
            (-24.1858, -65.2995),
            (-23.9800, -65.3450),
            (-23.8000, -65.3950),
            (-23.6500, -65.4080),
            (-23.5735, -65.3940),
        ],
    },
    {
        "nombre": "Perico → El Carmen",
        "coords": [
            (-24.3825, -65.0415),
            (-24.4100, -65.0900),
            (-24.4400, -65.1200),
            (-24.4350, -65.1980),
        ],
    },
    {
        "nombre": "Yuto → Calilegua",
        "coords": [
            (-23.8500, -64.8300),
            (-23.7500, -64.9200),
            (-23.6500, -65.0000),
            (-23.5500, -65.1000),
        ],
    },
    {
        "nombre": "Libertador → Humahuaca",
        "coords": [
            (-23.5000, -64.4500),
            (-23.3000, -64.7000),
            (-23.1500, -64.9000),
            (-23.1000, -65.0000),
        ],
    },
    {
        "nombre": "San Salvador → San Pedro",
        "coords": [
            (-24.1858, -65.2995),
            (-23.9300, -65.4000),
            (-23.6500, -65.5000),
            (-23.4000, -65.6000),
        ],
    },
    {
        "nombre": "Jujuy Capital → Libertador",
        "coords": [
            (-24.1858, -65.2995),
            (-24.1500, -65.2500),
            (-24.1200, -65.2000),
            (-24.1000, -65.1500),
        ],
    },
    {
        "nombre": "Tilcara → Purmamarca",
        "coords": [
            (-23.5735, -65.3940),
            (-23.5500, -65.3500),
            (-23.5000, -65.3000),
            (-23.4500, -65.2500),
        ],
    },
]

def load_demo_routes():
    for vinfo in viajes_info:
        v, created = ViajeDemo.objects.get_or_create(
            nombre=vinfo["nombre"],
            defaults={"descripcion": ""}
        )
        if created:
            print(f"Creado viaje demo: {v.nombre}")
        else:
            print(f"Ya existía viaje demo: {v.nombre}")

        # Eliminamos rutas viejas de ese viaje para evitar duplicados
        RutaDemo.objects.filter(viaje=v).delete()

        # Insertar coordenadas nuevas
        for idx, (lat, lon) in enumerate(vinfo["coords"], start=1):
            RutaDemo.objects.create(viaje=v, orden=idx, latitud=lat, longitud=lon)
        print(f"  → Insertadas {len(vinfo['coords'])} puntos para la ruta.")

if __name__ == "__main__":
    load_demo_routes()
    print("✅ Todas las rutas demo fueron cargadas.")
