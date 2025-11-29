from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Empresa

class RegistroEmpresaForm(UserCreationForm):
    nombre_empresa = forms.CharField(max_length=150, label='Nombre de la empresa')
    cuit = forms.CharField(max_length=20, label='CUIT')
    direccion = forms.CharField(max_length=200, required=False)
    contacto = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'EMPRESA'
        user.is_active = False  # hasta que confirme el correo
        if commit:
            user.save()
        return user


from .models import Viaje

# transporte/forms.py

from django import forms
from .models import Viaje, Chofer, Vehiculo, Carga # Asegúrate de importar todos

class FormViaje(forms.ModelForm):
    class Meta:
        model = Viaje
        # Los campos que el usuario DEBE seleccionar
        fields = ['origen', 'destino', 'fecha_salida', 'fecha_llegada_estimada', 'chofer', 'vehiculo', 'carga']
        
        # Widgets de fecha/hora
        widgets = {
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_llegada_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Filtramos choferes, vehículos y cargas de la empresa actual
        if empresa:
            # 💡 CORRECCIÓN SUGERIDA (Opción A): Filtrar usando el manager del modelo
            # (Asumiendo que Chofer, Vehiculo, Carga tienen un campo 'empresa')
            
            self.fields['chofer'].queryset = Chofer.objects.filter(empresa=empresa)
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa)
            self.fields['carga'].queryset = Carga.objects.filter(empresa=empresa)


from django import forms
from .models import Viaje

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            "empresa",
            "chofer",
            "vehiculo",
            "carga",
            "origen",
            "destino",
            "lat_origen",
            "lon_origen",
            "lat_destino",
            "lon_destino",
            "fecha_salida",
            "fecha_llegada_estimada",
            "estado",
        ]

        widgets = {
            "fecha_salida": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "fecha_llegada_estimada": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }



from .models import EquipoGPS

class EquipoGPSForm(forms.ModelForm):
    class Meta:
        model = EquipoGPS
        fields = ["nombre", "imei", "tipo", "vehiculo", "estado", "ultima_conexion"]
        widgets = {
            "ultima_conexion": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'patente', 'marca', 'modelo',
            'capacidad', 'consumo_promedio', 'costo_km',
            'empresa', 'estado'
        ]
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'patente': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'consumo_promedio': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_km': forms.NumberInput(attrs={'class': 'form-control'}),
        }
