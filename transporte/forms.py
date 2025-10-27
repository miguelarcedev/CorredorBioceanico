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

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = ['origen', 'destino', 'fecha_salida', 'fecha_llegada_estimada', 'chofer', 'vehiculo', 'carga']
        widgets = {
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_llegada_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        # Filtramos choferes, vehículos y cargas de la empresa actual
        if empresa:
            self.fields['chofer'].queryset = empresa.choferes.all()
            self.fields['vehiculo'].queryset = empresa.vehiculos.all()
            self.fields['carga'].queryset = empresa.cargas.all()
