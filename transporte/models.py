from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.urls import reverse
from geopy.distance import geodesic
from datetime import datetime


# ---------------------------
# MODELO DE USUARIO PERSONALIZADO
# ---------------------------
class Usuario(AbstractUser):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('EMPRESA', 'Empresa de Transporte'),
        ('CHOFER', 'Chofer'),
        ('FRONTERA', 'Agente de Frontera'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='EMPRESA')

     # NUEVO CAMPO
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    # fin nuevo
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


# ---------------------------
# MODELOS DE EMPRESA, CHOFER Y VEHÍCULO
# ---------------------------
class Empresa(models.Model):
    nombre = models.CharField(max_length=150)
    cuit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200, blank=True)
    contacto = models.CharField(max_length=100, blank=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='empresa')

    def __str__(self):
        return self.nombre


class Chofer(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento = models.CharField(max_length=15, unique=True)
    licencia_nro = models.CharField(max_length=30)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='choferes')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Vehiculo(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    capacidad = models.FloatField(help_text="Capacidad máxima en toneladas")
    consumo_promedio = models.FloatField(default=0, help_text="Consumo estimado (litros/km)")
    costo_km = models.FloatField(default=0, help_text="Costo operativo por km en ARS")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='vehiculos')

    estado = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('mantenimiento', 'En mantenimiento'),
        ('inactivo', 'Inactivo')
    ], default='activo')

    fecha_alta = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"




ESTADOS_EQUIPO = [
    ("online", "Online"),
    ("offline", "Offline"),
    ("mantenimiento", "En Mantenimiento"),
]

class EquipoGPS(models.Model):
    nombre = models.CharField(max_length=100)
    imei = models.CharField(max_length=30, unique=True)
    tipo = models.CharField(max_length=50, default="GPS")

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos"
    )

    estado = models.CharField(max_length=20, choices=ESTADOS_EQUIPO, default="offline")
    ultima_conexion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.imei})"


# ---------------------------
# MODELO DE CARGA
# ---------------------------
class Carga(models.Model):
    tipo = models.CharField(max_length=100)
    peso_aprox = models.FloatField()
    descripcion = models.TextField(blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cargas')

    def __str__(self):
        return f"{self.tipo} ({self.peso_aprox} tn)"


# ---------------------------
# MODELO DE VIAJE
# ---------------------------
class Viaje(models.Model):

    ESTADOS = [
        ("PROGRAMADO", "Programado"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ---------------------------------------
    # DATOS BASE DEL VIAJE
    # ---------------------------------------
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="viajes")
    chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE, related_name="viajes")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="viajes")
    carga = models.ForeignKey(Carga, on_delete=models.CASCADE, related_name="viajes")

    origen = models.CharField(max_length=150)
    destino = models.CharField(max_length=150)

    lat_origen = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon_origen = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lat_destino = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon_destino = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)


    fecha_salida = models.DateTimeField()
    fecha_llegada_estimada = models.DateTimeField()
    fecha_llegada_real = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="PROGRAMADO")

    # Ubicación en tiempo real (útil para monitoreo)
    ubicacion_actual = models.CharField(max_length=200, blank=True, null=True)

    # QR para trazabilidad
    codigo_qr = models.ImageField(upload_to="qrcodes/", blank=True, null=True)

    # ---------------------------------------
    # DATOS OPERATIVOS Y KPIs AUTOMATIZADOS
    # ---------------------------------------
    distancia_km = models.FloatField(default=0)
    kilometros_recorridos = models.FloatField(default=0)

    duracion_horas = models.FloatField(default=0)
    tiempo_total_horas = models.FloatField(default=0)

    consumo_promedio = models.FloatField(default=0, help_text="Litros por 100 km")
    velocidad_promedio = models.FloatField(default=0, help_text="km/h")

    costo_estimado = models.FloatField(default=0)
    costo_combustible = models.FloatField(default=0, help_text="Costo total de combustible en USD")

    litros_consumidos = models.FloatField(default=0, help_text="Litros de combustible utilizados en el viaje")
    precio_combustible = models.FloatField(default=1.5, help_text="Precio por litro en USD")


    # ---------------------------------------
    # MÉTODOS
    # ---------------------------------------
    def __str__(self):
        return f"Viaje {self.id} - {self.origen} → {self.destino}"

    def save(self, *args, **kwargs):
        crear_qr = False

        # Guardamos primero para obtener el ID
        if not self.pk:
            crear_qr = True

        super().save(*args, **kwargs)

        # Generación de QR con URL pública del viaje
        if crear_qr:
            url = f"https://corredor.now-dns.net{reverse('viaje_detalle', args=[self.id])}"
            qr_img = qrcode.make(url)

            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            file_name = f"viaje_{self.id}.png"

            self.codigo_qr.save(file_name, File(buffer), save=False)
            super().save(update_fields=["codigo_qr"])


# ---------------------------
# MODELOS DE POSICIÓN GPS Y ALERTAS
# ---------------------------

class PosicionGPS(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="posiciones")
    latitud = models.FloatField()
    longitud = models.FloatField()
    velocidad = models.FloatField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.viaje.id} @ {self.fecha_hora}"


class Alerta(models.Model):
    TIPOS = [
        ('DEMORA', 'Demora'),
        ('DESVIO', 'Desvío de ruta'),
        ('OTRO', 'Otro'),
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='alertas')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.CharField(max_length=255)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.mensaje}"


# ---------------------------
# MODELO DE CONTROL FRONTERIZO
# ---------------------------

class ControlFrontera(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='controles')
    agente = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'FRONTERA'})
    hora_cruce = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Control en frontera para {self.viaje.id}"



def calcular_metricas_viaje(viaje):
    """
    Calcula métricas de distancia, tiempo y velocidad a partir de las posiciones GPS registradas.
    """
    posiciones = viaje.posiciones.order_by('timestamp')
    if posiciones.count() < 2:
        return False  # No hay suficientes puntos

    # Calcular distancia total
    distancia_total = 0
    for i in range(1, posiciones.count()):
        punto1 = (posiciones[i-1].latitud, posiciones[i-1].longitud)
        punto2 = (posiciones[i].latitud, posiciones[i].longitud)
        distancia_total += geodesic(punto1, punto2).km

    # Calcular tiempo total
    tiempo_total = (posiciones.last().timestamp - posiciones.first().timestamp).total_seconds() / 3600
    velocidad_promedio = distancia_total / tiempo_total if tiempo_total > 0 else 0

    # Guardar en el modelo
    viaje.kilometros_recorridos = round(distancia_total, 2)
    viaje.tiempo_total_horas = round(tiempo_total, 2)
    viaje.velocidad_promedio = round(velocidad_promedio, 2)
    viaje.save(update_fields=['kilometros_recorridos', 'tiempo_total_horas', 'velocidad_promedio'])
    return True

#agrego
class Novedad(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='novedades/')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']  # Las más nuevas primero

    def __str__(self):
        return self.titulo

