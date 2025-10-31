

# Register your models here.

from django.contrib import admin
from .models import Usuario, Empresa, Chofer, Vehiculo, Carga, Viaje, PosicionGPS, Alerta, ControlFrontera,RegistroUbicacion

admin.site.register(Usuario)
admin.site.register(Empresa)
admin.site.register(Chofer)
admin.site.register(Vehiculo)
admin.site.register(Carga)
admin.site.register(Viaje)
admin.site.register(PosicionGPS)
admin.site.register(Alerta)
admin.site.register(ControlFrontera)
admin.site.register(RegistroUbicacion)
