from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.urls import reverse


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
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='vehiculos')

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"


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
        ('PROGRAMADO', 'Programado'),
        ('EN_CURSO', 'En curso'),
        ('FINALIZADO', 'Finalizado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origen = models.CharField(max_length=150)
    destino = models.CharField(max_length=150)
    fecha_salida = models.DateTimeField()
    fecha_llegada_estimada = models.DateTimeField()
    fecha_llegada_real = models.DateTimeField(null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='viajes')
    chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE, related_name='viajes')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='viajes')
    carga = models.ForeignKey(Carga, on_delete=models.CASCADE, related_name='viajes')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PROGRAMADO')
    ubicacion_actual = models.CharField(max_length=200, blank=True, null=True)
    codigo_qr = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def __str__(self):
        return f"Viaje {self.id} - {self.origen} → {self.destino}"
    
    def save(self, *args, **kwargs):
        # Guardamos primero para tener el ID disponible
        super().save(*args, **kwargs)
        if not self.codigo_qr:
            # Generamos URL del detalle del viaje
            url = f"https://corredor.now-dns.net{reverse('viaje_detalle', args=[self.id])}"
            qr_img = qrcode.make(url)
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            file_name = f'viaje_{self.id}.png'
            self.codigo_qr.save(file_name, File(buffer), save=False)
            super().save(update_fields=['codigo_qr'])


# ---------------------------
# MODELOS DE POSICIÓN GPS Y ALERTAS
# ---------------------------
class PosicionGPS(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='posiciones')
    latitud = models.FloatField()
    longitud = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.viaje.id} ({self.latitud}, {self.longitud})"


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


class RegistroUbicacion(models.Model):
    viaje = models.ForeignKey('Viaje', on_delete=models.CASCADE, related_name='registros')
    lat = models.FloatField()
    lon = models.FloatField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.viaje.id} @ {self.fecha_hora:%Y-%m-%d %H:%M:%S}"


# ---------------------------
# MODO DEMO - VIAJES SIMULADOS
# ---------------------------
class ViajeDemo(models.Model):
    """Viajes de demostración con rutas predefinidas."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150, help_text="Ej: San Salvador → Perico")
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"[DEMO] {self.nombre}"


class RutaDemo(models.Model):
    """Coordenadas predefinidas para simular el recorrido de un viaje demo."""
    viaje = models.ForeignKey(ViajeDemo, on_delete=models.CASCADE, related_name='rutas')
    orden = models.PositiveIntegerField(help_text="Orden del punto en la ruta")
    latitud = models.FloatField()
    longitud = models.FloatField()

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"Ruta {self.orden} ({self.latitud}, {self.longitud}) - {self.viaje.nombre}"


class PosicionDemo(models.Model):
    """Posiciones simuladas generadas durante la demostración."""
    viaje = models.ForeignKey(ViajeDemo, on_delete=models.CASCADE, related_name='posiciones')
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[DEMO] {self.viaje.nombre} ({self.latitud}, {self.longitud})"
