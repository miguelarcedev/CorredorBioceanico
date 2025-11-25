
from .forms import ViajeForm, RegistroEmpresaForm, VehiculoForm, EquipoGPSForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.dateparse import parse_date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count
from datetime import datetime, timedelta
from .models import ViajeDemo, RutaDemo, PosicionDemo, EquipoGPS, Chofer, Vehiculo
from .models import Viaje, Empresa, Usuario, RegistroUbicacion
import requests




@login_required
def home(request):
        
    return render(request, 'transporte/home.html')


@login_required
def dashboard(request):
    # Si el usuario es una empresa, mostrar sus viajes
    if hasattr(request.user, 'empresa'):
        empresa = request.user.empresa
        viajes = Viaje.objects.filter(empresa=empresa).order_by('-fecha_salida')
    else:
        viajes = Viaje.objects.all().order_by('-fecha_salida')  # solo admin
    
    return render(request, 'transporte/dashboard.html', {'viajes': viajes})



# LISTA

@login_required
def viaje_list(request):
    viajes = Viaje.objects.all().order_by('-fecha_salida')
    return render(request, 'viajes/viaje_list.html', {'viajes': viajes})


# CREAR

@login_required
def viaje_create(request):
    if request.method == 'POST':
        form = ViajeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('viaje_list')
    else:
        form = ViajeForm()
    return render(request, 'viajes/viaje_form.html', {'form': form})


# EDITAR

@login_required
def viaje_edit(request, pk):
    viaje = get_object_or_404(Viaje, pk=pk)
    if request.method == 'POST':
        form = ViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            form.save()
            return redirect('viaje_list')
    else:
        form = ViajeForm(instance=viaje)
    return render(request, 'viajes/viaje_form.html', {'form': form, 'viaje': viaje})


# ELIMINAR

@login_required
def viaje_delete(request, pk):
    viaje = get_object_or_404(Viaje, pk=pk)
    if request.method == 'POST':
        viaje.delete()
        return redirect('viaje_list')
    return render(request, 'viajes/viaje_confirm_delete.html', {'viaje': viaje})


# DETALLE

@login_required
def viaje_detalle(request, pk):
    viaje = get_object_or_404(Viaje, pk=pk)
    return render(request, 'viajes/viaje_detalle.html', {'viaje': viaje})



def registro(request):
    if request.method == 'POST':
        form = RegistroEmpresaForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False # Asegurar que la cuenta no esté activa hasta que se haga clic
            user.save()

            # Crear la empresa vinculada
            Empresa.objects.create(
                nombre=form.cleaned_data['nombre_empresa'],
                cuit=form.cleaned_data['cuit'],
                direccion=form.cleaned_data.get('direccion', ''),
                contacto=form.cleaned_data.get('contacto', ''),
                usuario=user
            )

            # ... (Lógica de envío de correo) ...
            dominio = get_current_site(request).domain
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link_activacion = f"http://{dominio}/activar/{uid}/{token}/"

            mensaje = render_to_string('transporte/email_activacion.txt', {
                'usuario': user,
                'link_activacion': link_activacion,
            })
            send_mail(
                'Activación de cuenta - Empresa de Transporte de carga',
                mensaje,
                None,
                [user.email],
            )
            
            # 💡 CAMBIO 1: Usar messages y redirect
            messages.success(request, '¡Registro exitoso! Revisa tu correo electrónico para el enlace de activación y completa el proceso.')
            return redirect('login') # Redirige al usuario al login
    else:
        form = RegistroEmpresaForm()

    return render(request, 'transporte/registro.html', {'form': form})



def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        # Asegúrate de importar tu modelo Usuario, por ejemplo: from .models import Usuario
        user = Usuario.objects.get(pk=uid) 
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        
        # 💡 CAMBIO 2: Mensaje de éxito y redirección a login
        messages.success(request, 'Tu cuenta ha sido activada correctamente. ¡Ya puedes iniciar sesión!')
        return redirect('login') 
    else:
        # 💡 CAMBIO 3: Mensaje de error y redirección a login
        messages.error(request, 'El enlace de activación no es válido o ha expirado. Por favor, contacta a soporte.')
        return redirect('login') # También redirige a login para evitar página en blanco



@login_required
def actualizar_ubicacion(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/actualizar_ubicacion.html', {'viaje': viaje})



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



def monitor_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/monitor_viaje.html', {'viaje': viaje})



def monitoreo_viaje(request, viaje_id):
    """Muestra el mapa con el recorrido en tiempo real."""
    viaje = get_object_or_404(Viaje, id=viaje_id)
    return render(request, 'transporte/monitoreo_viaje.html', {'viaje': viaje})


def demo_viaje(request):
    viajes = Viaje.objects.filter(estado="PROGRAMADO")
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



# -----------------------------
# MONITOREO REAL
# -----------------------------
@login_required
def monitoreo_real(request):
    viajes = Viaje.objects.filter(estado__in=["EN_CURSO", "PROGRAMADO"])
    return render(request, "transporte/monitoreo_real.html", {"viajes": viajes})


# -----------------------------
# MONITOREO DEMO
# -----------------------------

def monitoreo_demo(request):
    viajes = Viaje.objects.filter(estado="EN_CURSO")
    context = {
        "viajes": viajes
    }
    return render(request, "transporte/demo_viaje.html", context)



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





# ================================
#  API: obtener ruta entre puntos
# ================================

@csrf_exempt
def obtener_ruta(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    if not start or not end:
        return JsonResponse({'error': 'Faltan coordenadas'}, status=400)

    try:
        # Limpieza mínima
        start = start.replace(" ", "")
        end = end.replace(" ", "")

        lat1, lon1 = map(float, start.split(","))
        lat2, lon2 = map(float, end.split(","))

    except Exception as e:
        print("ERROR parseando coordenadas:", e)
        return JsonResponse({'error': 'Coordenadas inválidas'}, status=400)

    # Formato ORS: [lon, lat]
    coordinates = [[lon1, lat1], [lon2, lat2]]

    # =======================================================
    # 1) INTENTAR OPENROUTESERVICE
    # =======================================================
    API_KEY = "TU_API_KEY"

    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {"Authorization": API_KEY, "Content-Type": "application/json"}

        payload = {
            "coordinates": coordinates,
            "units": "m"
        }

        r = requests.post(url, json=payload, headers=headers, timeout=12)
        data = r.json()

        print("DEBUG ORS →", data)

        if "features" in data:
            coords = data["features"][0]["geometry"]["coordinates"]

            ruta = [[lat, lon] for lon, lat in coords]

            if len(ruta) >= 2:
                return JsonResponse(ruta, safe=False)

    except Exception as e:
        print("ORS ERROR:", e)

    # =======================================================
    # 2) FALLBACK OSRM (mucho más estable)
    # =======================================================
    try:
        osrm_url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{lon1},{lat1};{lon2},{lat2}"
            f"?overview=full&geometries=geojson"
        )

        r = requests.get(osrm_url, timeout=12)
        d = r.json()

        print("DEBUG OSRM →", d)

        if "routes" in d and d["routes"]:
            coords = d["routes"][0]["geometry"]["coordinates"]

            ruta = [[lat, lon] for lon, lat in coords]

            if len(ruta) >= 2:
                return JsonResponse(ruta, safe=False)

    except Exception as e:
        print("OSRM ERROR:", e)

    # =======================================================
    # FALLÓ TODO
    # =======================================================
    return JsonResponse({'error': 'No se pudo obtener la ruta real'}, status=500)



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



def panel_analitico(request):
    viajes = Viaje.objects.all()

    data = {
        'total_viajes': viajes.count(),
        'distancia_total': viajes.aggregate(Sum('kilometros_recorridos'))['kilometros_recorridos__sum'] or 0,
        'distancia_promedio': viajes.aggregate(Avg('kilometros_recorridos'))['kilometros_recorridos__avg'] or 0,
        'velocidad_promedio': viajes.aggregate(Avg('velocidad_promedio'))['velocidad_promedio__avg'] or 0,
        'tiempo_promedio': viajes.aggregate(Avg('tiempo_total_horas'))['tiempo_total_horas__avg'] or 0,
        'alertas': viajes.values('estado').annotate(total=Count('alertas')),
        'lista_viajes': viajes.order_by('-fecha_salida')[:10],
    }

    return render(request, 'analitico/panel.html', {'data': data})


# ================================
#  CRUD COMPLETO -- EquiposGPS
# ================================

# LISTA
@login_required
def equipos_list(request):
    equipos = EquipoGPS.objects.all().order_by("nombre")
    return render(request, "equipos/equipos.html", {"equipos": equipos})


# DETALLE
@login_required
def equipos_detalle(request, pk):
    equipo = get_object_or_404(EquipoGPS, pk=pk)
    return render(request, "equipos/equipos_detalle.html", {"equipo": equipo})


# CREAR
@login_required
def equipos_crear(request):
    if request.method == "POST":
        form = EquipoGPSForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("equipos_list")
    else:
        form = EquipoGPSForm()

    return render(request, "equipos/equipos_form.html", {"form": form, "accion": "Crear"})


# EDITAR
@login_required
def equipos_editar(request, pk):
    equipo = get_object_or_404(EquipoGPS, pk=pk)

    if request.method == "POST":
        form = EquipoGPSForm(request.POST, instance=equipo)
        if form.is_valid():
            form.save()
            return redirect("equipos_list")
    else:
        form = EquipoGPSForm(instance=equipo)

    return render(request, "equipos/equipos_form.html", {"form": form, "accion": "Editar"})


# ELIMINAR
@login_required
def equipos_eliminar(request, pk):
    equipo = get_object_or_404(EquipoGPS, pk=pk)

    if request.method == "POST":
        equipo.delete()
        return redirect("equipos_list")

    return render(request, "equipos/equipos_eliminar.html", {"equipo": equipo})


# ================================
#  CRUD COMPLETO -- VEHICULOS
# ================================

# LISTA
@login_required
def vehiculo_list(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')
    return render(request, 'vehiculos/vehiculo_list.html', {'vehiculos': vehiculos})


# CREAR
@login_required
def vehiculo_create(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vehiculo_list')
    else:
        form = VehiculoForm()

    return render(request, 'vehiculos/vehiculo_form.html', {
        'form': form,
        'titulo': 'Registrar Vehículo',
        'boton': 'Guardar'
    })


# EDITAR
@login_required
def vehiculo_update(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            return redirect('vehiculo_list')
    else:
        form = VehiculoForm(instance=vehiculo)

    return render(request, 'vehiculos/vehiculo_form.html', {
        'form': form,
        'titulo': 'Editar Vehículo',
        'boton': 'Actualizar'
    })


# ELIMINAR
@login_required
def vehiculo_delete(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    if request.method == 'POST':
        vehiculo.delete()
        return redirect('vehiculo_list')

    return render(request, 'vehiculos/vehiculo_confirm_delete.html', {
        'vehiculo': vehiculo
    })


# ================================
#  REPORTES -- VIAJES
# ================================

def reporte_viajes_completados(request):
    
    viajes = Viaje.objects.filter(estado="FINALIZADO").order_by("-fecha_salida")
    empresas = Empresa.objects.all()
    choferes = Chofer.objects.all()

    # FILTROS (opcionales)
    fecha_desde = request.GET.get("desde")
    fecha_hasta = request.GET.get("hasta")
    empresa_id = request.GET.get("empresa")
    chofer_id = request.GET.get("chofer")

    if fecha_desde:
        viajes = viajes.filter(fecha_salida__date__gte=parse_date(fecha_desde))

    if fecha_hasta:
        viajes = viajes.filter(fecha_salida__date__lte=parse_date(fecha_hasta))

    if empresa_id and empresa_id != "0":
        viajes = viajes.filter(empresa_id=empresa_id)

    if chofer_id and chofer_id != "0":
        viajes = viajes.filter(chofer_id=chofer_id)

    context = {
        "viajes": viajes,
        "empresas": empresas,
        "choferes": choferes,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "empresa_id": empresa_id,
        "chofer_id": chofer_id,
    }

    return render(request, "reportes/reporte_viajes_completados.html", context)
