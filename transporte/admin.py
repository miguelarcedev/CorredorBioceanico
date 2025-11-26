

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario,
    Empresa,
    Chofer,
    Vehiculo,
    Carga,
    Viaje,
    ViajeDemo,
    PosicionGPS,
    Alerta,
    ControlFrontera,
    RegistroUbicacion,
    PosicionDemo,
)

# 👉 Admin para el usuario personalizado
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # Campos que se ven en el listado
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')

    # Secciones del formulario de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información extra', {'fields': ('rol', 'photo')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información extra', {'fields': ('rol', 'photo')}),
    )


# 👉 Resto de modelos del sistema
admin.site.register(Empresa)
admin.site.register(Chofer)
admin.site.register(Vehiculo)
admin.site.register(Carga)
admin.site.register(Viaje)
admin.site.register(ViajeDemo)
admin.site.register(PosicionGPS)
admin.site.register(PosicionDemo)
admin.site.register(Alerta)
admin.site.register(ControlFrontera)
admin.site.register(RegistroUbicacion)

