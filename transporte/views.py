

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
    return render(request, 'transporte/actualizar_ubicacion.html', {'viaje': viaje})






# transporte/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Viaje, RegistroUbicacion

""" @csrf_exempt
def actualizar_ubicacion_api(request, viaje_id):
    if request.method == 'POST':
        try:
            lat = float(request.POST.get('lat'))
            lon = float(request.POST.get('lon'))
            viaje = Viaje.objects.get(id=viaje_id)

            viaje.ubicacion_actual = f"{lat},{lon}"
            viaje.save(update_fields=['ubicacion_actual'])

            RegistroUbicacion.objects.create(viaje=viaje, lat=lat, lon=lon)

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}) """


# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

# ======================================================
#   API: Actualizar (enviar) nueva ubicación
# ======================================================
@csrf_exempt
def actualizar_ubicacion_api(request, viaje_id):
    """
    Recibe una nueva ubicación (lat, lon) en formato JSON y la guarda en la BD.
    Retorna estado y la ubicación registrada con timestamp.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lat = data.get("lat")
            lon = data.get("lon")

            if lat is None or lon is None:
                return JsonResponse({"error": "Faltan parámetros lat/lon"}, status=400)

            viaje = Viaje.objects.get(pk=viaje_id)

            ubicacion = RegistroUbicacion.objects.create(
                viaje=viaje,
                lat=lat,
                lon=lon,
                fecha_hora=timezone.now()
            )

            return JsonResponse({
                "status": "ok",
                "ubicacion": {
                    "lat": ubicacion.lat,
                    "lon": ubicacion.lon,
                    "fecha_hora": ubicacion.fecha_hora.isoformat(),
                }
            })

        except Viaje.DoesNotExist:
            return JsonResponse({"error": "Viaje no encontrado"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


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



from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Viaje, RegistroUbicacion

def monitoreo_viaje(request, viaje_id):
    """Muestra el mapa con el recorrido en tiempo real."""
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/monitoreo_viaje.html', {'viaje': viaje})

from django.shortcuts import render, get_object_or_404
from .models import Viaje


from .models import ViajeDemo  # asegurate de importar el modelo correcto

def demo_viaje(request):
    viajes = ViajeDemo.objects.filter(estado="PROGRAMADO")  # 👈 usamos el modelo demo
    return render(request, "transporte/demo_viaje.html", {"viajes": viajes})





def obtener_ubicaciones(request, viaje_id):
    """
    Devuelve las ubicaciones asociadas al viaje en formato JSON.
    Incluye fecha y hora en formato ISO para el frontend.
    """
    ubicaciones = RegistroUbicacion.objects.filter(viaje_id=viaje_id).order_by('fecha_hora')
    data = {
        "ubicaciones": [
            {
                "lat": u.lat,
                "lon": u.lon,
                "fecha_hora": u.fecha_hora.isoformat() if u.fecha_hora else None,
            }
            for u in ubicaciones
        ]
    }
    return JsonResponse(data)


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Viaje, ViajeDemo, RutaDemo, RegistroUbicacion
from datetime import datetime

# -----------------------------
# MONITOREO REAL
# -----------------------------
def monitoreo_real(request):
    viajes = Viaje.objects.filter(estado__in=["EN_CURSO", "PROGRAMADO"])
    return render(request, "transporte/monitoreo_real.html", {"viajes": viajes})


# -----------------------------
# MONITOREO DEMO
# -----------------------------
def monitoreo_demo(request):
    viajes = ViajeDemo.objects.all()
    return render(request, "transporte/demo_viaje.html", {"viajes": viajes})


# -----------------------------
# API para devolver las coordenadas demo
# -----------------------------
def api_ruta_demo(request, viaje_id):
    viaje = get_object_or_404(ViajeDemo, id=viaje_id)
    rutas = RutaDemo.objects.filter(viaje=viaje).order_by("orden")
    data = [
        {
            "lat": r.latitud,
            "lon": r.longitud,
            "orden": r.orden,
        }
        for r in rutas
    ]
    return JsonResponse({"ruta": data})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PosicionDemo
import json

@csrf_exempt
def registrar_posicion_demo(request):
    """
    Guarda una posición de simulación (modo demo)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            viaje_id = data.get('viaje_id')
            lat = data.get('lat')
            lon = data.get('lon')

            if not all([viaje_id, lat, lon]):
                return JsonResponse({'error': 'Datos incompletos'}, status=400)

            PosicionDemo.objects.create(
                viaje_id=viaje_id,
                latitud=lat,
                longitud=lon
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from .models import ViajeDemo, PosicionDemo

# ================================
#  API: obtener ruta entre puntos
# ================================
@csrf_exempt
def obtener_ruta(request):
    lat1 = request.GET.get("start", "").split(",")[0]
    lon1 = request.GET.get("start", "").split(",")[1]
    lat2 = request.GET.get("end", "").split(",")[0]
    lon2 = request.GET.get("end", "").split(",")[1]

    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except Exception:
        return JsonResponse({"error": "Coordenadas inválidas"}, status=400)

    # ========================
    # 1️⃣ Intentar con ORS
    # ========================
    ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
    ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImFlNmEzYWMxNTQ3MDRkYTE5ZGIwMzhiNzU4OGU4ZTY2IiwiaCI6Im11cm11cjY0In0="

    payload = {
        "coordinates": [[lon1, lat1], [lon2, lat2]],
        "radiuses": [1000, 1000]  # <-- permite buscar calles hasta 1 km del punto
    }

    headers = {
        "Authorization": ORS_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(ORS_URL, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            geometry = data["features"][0]["geometry"]["coordinates"]
            ruta = [[coord[1], coord[0]] for coord in geometry]
            return JsonResponse(ruta, safe=False)

        else:
            print("⚠️ ORS falló:", response.text)
            raise Exception("ORS error")

    except Exception as e:
        print("Error en OpenRouteService:", e)

    # ========================
    # 2️⃣ Fallback con OSRM
    # ========================
    try:
        osrm_url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        osrm_response = requests.get(osrm_url, timeout=15)

        if osrm_response.status_code == 200:
            data = osrm_response.json()
            coords = data["routes"][0]["geometry"]["coordinates"]
            ruta = [[lat, lon] for lon, lat in coords]
            print("✅ Ruta obtenida por OSRM")
            return JsonResponse(ruta, safe=False)
        else:
            print("⚠️ OSRM falló:", osrm_response.text)
            return JsonResponse({"error": "Error al consultar OSRM"}, status=500)

    except Exception as e:
        print("Error en OSRM:", e)
        return JsonResponse({"error": "Error al consultar ruta externa", "detalle": str(e)}, status=500)


# ================================
#  API: lista de viajes demo
# ================================
def lista_viajes_demo(request):
    viajes = ViajeDemo.objects.all().prefetch_related("posiciones")
    return JsonResponse([
        {
            "id": v.id,
            "origen": v.origen,
            "destino": v.destino,
            "estado": v.estado,
            "posiciones": [
                {"latitud": p.latitud, "longitud": p.longitud, "timestamp": p.timestamp}
                for p in v.posiciones.all()
            ]
        } for v in viajes
    ], safe=False)

