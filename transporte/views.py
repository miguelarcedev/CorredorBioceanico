

# Create your views here.

# transporte/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Viaje


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Viaje, Empresa, Usuario

@login_required
def dashboard(request):
    # Si el usuario es una empresa, mostrar sus viajes
    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        viajes = Viaje.objects.filter(empresa=empresa).order_by('-fecha_salida')
    else:
        viajes = Viaje.objects.all().order_by('-fecha_salida')  # solo admin
    
    return render(request, 'transporte/dashboard.html', {'viajes': viajes})


@login_required
def viaje_list(request):
    empresa = request.user.empresa if hasattr(request.user, 'empresa') else None
    viajes = Viaje.objects.filter(empresa=empresa) if empresa else Viaje.objects.all()
    return render(request, 'transporte/viaje_list.html', {'viajes': viajes})


@login_required
def viaje_detalle(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/viaje_detalle.html', {'viaje': viaje})


from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse

from .forms import RegistroEmpresaForm

def registro(request):
    if request.method == 'POST':
        form = RegistroEmpresaForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear la empresa vinculada
            Empresa.objects.create(
                nombre=form.cleaned_data['nombre_empresa'],
                cuit=form.cleaned_data['cuit'],
                direccion=form.cleaned_data.get('direccion', ''),
                contacto=form.cleaned_data.get('contacto', ''),
                usuario=user
            )

            # Enviar correo de activación
            dominio = get_current_site(request).domain
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link_activacion = f"http://{dominio}/activar/{uid}/{token}/"

            mensaje = render_to_string('transporte/email_activacion.txt', {
                'usuario': user,
                'link_activacion': link_activacion,
            })
            send_mail(
                'Activación de cuenta - Corredor Bioceánico',
                mensaje,
                None,
                [user.email],
            )
            return HttpResponse("<h4>Registro exitoso. Revisa tu correo para activar tu cuenta.</h4>")
    else:
        form = RegistroEmpresaForm()

    return render(request, 'transporte/registro.html', {'form': form})


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse("<h4>Cuenta activada correctamente. Ya puedes iniciar sesión.</h4>")
    else:
        return HttpResponse("<h4>El enlace de activación no es válido o ha expirado.</h4>")


from django.contrib import messages
from django.shortcuts import redirect
from .forms import ViajeForm

@login_required
def viaje_crear(request):
    if not hasattr(request.user, 'empresa'):
        messages.error(request, "Solo las empresas pueden registrar viajes.")
        return redirect('dashboard')

    empresa = request.user.empresa

    if request.method == 'POST':
        form = ViajeForm(request.POST, empresa=empresa)
        if form.is_valid():
            viaje = form.save(commit=False)
            viaje.empresa = empresa
            viaje.estado = 'PROGRAMADO'
            viaje.save()
            messages.success(request, "El viaje se registró correctamente.")
            return redirect('viaje_detalle', viaje_id=viaje.id)
    else:
        form = ViajeForm(empresa=empresa)

    return render(request, 'transporte/viaje_crear.html', {'form': form})

@login_required
def actualizar_ubicacion(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)

    if request.method == 'POST':
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        if lat and lon:
            viaje.ubicacion_actual = f"{lat}, {lon}"
            viaje.save(update_fields=['ubicacion_actual'])
            messages.success(request, "Ubicación actualizada correctamente.")
        return redirect('viaje_detalle', viaje_id=viaje.id)

    return render(request, 'transporte/actualizar_ubicacion.html', {'viaje': viaje})


# transporte/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Viaje, RegistroUbicacion

@csrf_exempt
def actualizar_ubicacion_api(request, viaje_id):
    if request.method == 'POST':
        try:
            lat = float(request.POST.get('lat'))
            lon = float(request.POST.get('lon'))
            viaje = Viaje.objects.get(id=viaje_id)

            # Actualizamos ubicación actual en Viaje
            viaje.ubicacion_actual = f"{lat},{lon}"
            viaje.ultima_actualizacion = timezone.now()
            viaje.save(update_fields=['ubicacion_actual', 'ultima_actualizacion'])

            # Guardamos registro histórico
            RegistroUbicacion.objects.create(viaje=viaje, lat=lat, lon=lon)

            return JsonResponse({'status': 'ok', 'mensaje': 'Ubicación actualizada'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})


# transporte/views.py
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

def registros_api(request, viaje_id):
    # GET: devuelve todos los registros del viaje en JSON
    try:
        viaje = Viaje.objects.get(id=viaje_id)
    except Viaje.DoesNotExist:
        return JsonResponse({'status':'error','mensaje':'Viaje no encontrado'}, status=404)

    registros = viaje.registros.all().values('lat', 'lon', 'fecha_hora')
    # Serializamos a lista para JS
    data = list(registros)
    return JsonResponse({'status':'ok', 'registros': data}, encoder=DjangoJSONEncoder)



# transporte/views.py
from django.shortcuts import render, get_object_or_404

def monitor_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/monitor_viaje.html', {'viaje': viaje})
