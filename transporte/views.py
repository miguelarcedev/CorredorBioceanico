
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
from .models import Viaje, Empresa, Usuario, EquipoGPS, Chofer, Vehiculo
import requests

#grego
from .models import Novedad


@login_required
def home(request):
    #agrego
    novedades = Novedad.objects.all()[:10]  # trae las últimas 10  
     
    return render(request, 'transporte/home.html', {
        'novedades': novedades
    })


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




# -----------------------------
# MONITOREO DEMO
# -----------------------------

def monitoreo_demo(request):
    viajes = Viaje.objects.filter(estado="EN_CURSO")
    context = {
        "viajes": viajes
    }
    return render(request, "transporte/demo_viaje.html", context)






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


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Viaje, PosicionGPS

@csrf_exempt
def guardar_posicion(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        viaje_id = data.get("viaje_id")
        lat = data.get("latitud")
        lon = data.get("longitud")
        velocidad = data.get("velocidad", 0)

        viaje = Viaje.objects.get(id=viaje_id)

        PosicionGPS.objects.create(
            viaje=viaje,
            latitud=lat,
            longitud=lon,
            velocidad=velocidad
        )

        return JsonResponse({"ok": True})

    except Viaje.DoesNotExist:
        return JsonResponse({"error": "Viaje no encontrado"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def finalizar_viaje(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        viaje_id = data.get("viaje_id")

        viaje = Viaje.objects.get(id=viaje_id)

        # Cambiar estado a "FINALIZADO"
        viaje.estado = "FINALIZADO"
        viaje.save()

        return JsonResponse({"ok": True})

    except Viaje.DoesNotExist:
        return JsonResponse({"error": "Viaje no encontrado"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Viaje, PosicionGPS
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def ver_mapa_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    puntos = PosicionGPS.objects.filter(viaje=viaje).order_by("fecha_hora")

    datos = []
    total_dist = 0
    velocidades = []

    ultimo = None

    for p in puntos:
        datos.append({
            "lat": float(p.latitud),
            "lon": float(p.longitud),
            "vel": float(p.velocidad),
            "t": p.fecha_hora.strftime("%H:%M:%S")
        })

        velocidades.append(p.velocidad)

        if ultimo:
            total_dist += haversine(
                ultimo.latitud, ultimo.longitud,
                p.latitud, p.longitud
            )
        ultimo = p

    resumen = {
        "distancia_total": round(total_dist, 2),
        "velocidad_max": round(max(velocidades), 2) if velocidades else 0,
        "velocidad_min": round(min(velocidades), 2) if velocidades else 0,
        "velocidad_promedio": round(sum(velocidades)/len(velocidades), 2) if velocidades else 0,
    }

    return render(request, "reportes/ver_mapa_viaje.html", {
        "viaje": viaje,
        "puntos": datos,
        "resumen": resumen
    })


from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.http import HttpResponse
from .models import Viaje


def exportar_pdf_viaje(request, viaje_id):
    viaje = Viaje.objects.get(id=viaje_id)

    # ---------------------------------------------------------------------
    #  SANEAR valores None → evitar que KPIs queden vacíos o generen error
    # ---------------------------------------------------------------------
    def safe(v, fmt="{:.2f}"):
        if v is None:
            return "—"
        try:
            return fmt.format(v)
        except:
            return str(v)

    # DEFAULTS SI EL VIAJE AÚN NO CARGÓ TODO
    km = safe(viaje.kilometros_recorridos)
    vel_prom = safe(viaje.velocidad_promedio, "{:.1f}")
    dur_hs = safe(viaje.tiempo_total_horas)
    cons = safe(viaje.consumo_promedio)
    costo_comb = safe(viaje.costo_combustible)
    costo_total = safe(viaje.costo_estimado)

    # ---------------------------------------------------------------------
    #   RESPONSE
    # ---------------------------------------------------------------------
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Viaje_{viaje.id}.pdf"'

    doc = SimpleDocTemplate(
        response, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # ----- Estilos minimalistas -----
    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=15,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.black,
        spaceAfter=6,
    )

    texto = ParagraphStyle(
        "Texto",
        parent=styles["BodyText"],
        fontSize=11,
        leading=15,
    )

    # ----- Separador minimalista -----
    def sep():
        return Table(
            [[""]],
            colWidths=[450],
            style=[
                ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.85, 0.85, 0.85)),
                ('INNER_PADDING', (0, 0), (-1, -1), 1),
            ],
        )

    story = []

    # =====================================================================
    #                         TÍTULO
    # =====================================================================
    story.append(Paragraph("REPORTE DEL VIAJE", titulo))
    story.append(sep())
    story.append(Spacer(1, 15))

    # =====================================================================
    #                 INFORMACIÓN GENERAL DEL VIAJE
    # =====================================================================
    story.append(Paragraph("Información del Viaje", subtitulo))
    info_html = f"""
        <b>Origen:</b> {viaje.origen}<br/>
        <b>Destino:</b> {viaje.destino}<br/>
        <b>Salida:</b> {viaje.fecha_salida.strftime("%d/%m/%Y %H:%M")}<br/>
        <b>Llegada real:</b> {viaje.fecha_llegada_real.strftime("%d/%m/%Y %H:%M") if viaje.fecha_llegada_real else "—"}<br/>
        <b>Estado:</b> {viaje.estado}<br/>
    """
    story.append(Paragraph(info_html, texto))
    story.append(Spacer(1, 10))
    story.append(sep())
    story.append(Spacer(1, 15))

    # =====================================================================
    #                            CHOFER
    # =====================================================================
    story.append(Paragraph("Chofer", subtitulo))
    story.append(Paragraph(
        f"<b>Nombre:</b> {viaje.chofer.nombre} {viaje.chofer.apellido}<br/>"
        f"<b>Documento:</b> {viaje.chofer.documento}<br/>"
        f"<b>Licencia:</b> {viaje.chofer.licencia_nro}",
        texto
    ))
    story.append(Spacer(1, 15))
    story.append(sep())
    story.append(Spacer(1, 15))

    # =====================================================================
    #                            VEHÍCULO
    # =====================================================================
    story.append(Paragraph("Vehículo", subtitulo))
    story.append(Paragraph(
        f"<b>Patente:</b> {viaje.vehiculo.patente}<br/>"
        f"<b>Marca/Modelo:</b> {viaje.vehiculo.marca} {viaje.vehiculo.modelo}<br/>"
        f"<b>Capacidad:</b> {viaje.vehiculo.capacidad} tn<br/>"
        f"<b>Estado:</b> {viaje.vehiculo.estado}",
        texto
    ))
    story.append(Spacer(1, 15))
    story.append(sep())
    story.append(Spacer(1, 15))

    # =====================================================================
    #                               CARGA
    # =====================================================================
    story.append(Paragraph("Carga", subtitulo))
    story.append(Paragraph(
        f"<b>Tipo:</b> {viaje.carga.tipo}<br/>"
        f"<b>Peso aprox.:</b> {viaje.carga.peso_aprox} tn<br/>"
        f"<b>Descripción:</b> {viaje.carga.descripcion or '—'}",
        texto
    ))
    story.append(Spacer(1, 15))
    story.append(sep())
    story.append(Spacer(1, 20))

    # =====================================================================
    #                         KPIs DEL VIAJE
    # =====================================================================
    story.append(Paragraph("Indicadores del Viaje (KPIs)", subtitulo))

    tabla_kpi = Table(
        [
            ["Indicador", "Valor"],
            ["Kilómetros recorridos", km],
            ["Velocidad promedio", vel_prom + " km/h"],
            ["Duración total", dur_hs + " h"],
            ["Consumo promedio", cons + " L/100km"],
            ["Costo combustible", costo_comb + " USD"],
            ["Costo total estimado", costo_total + " USD"],
        ],
        colWidths=[220, 200],
        style=[
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('INNER_PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ],
    )

    story.append(tabla_kpi)
    story.append(Spacer(1, 25))

    # =====================================================================
    #                                 PIE
    # =====================================================================
    story.append(Paragraph(
        "<i>Este informe fue generado automáticamente por el sistema de gestión de transporte.</i>",
        styles["Italic"]
    ))

    doc.build(story)
    return response
