

# Register your models here.

from django.contrib import admin
from .models import Usuario, Empresa, Chofer, Vehiculo, Carga, Viaje, PosicionGPS, Alerta, ControlFrontera,RegistroUbicacion
from django.contrib.auth.models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')

admin.site.register(User, UserAdmin)


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
