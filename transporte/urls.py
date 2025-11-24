from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #path('', views.dashboard, name='dashboard'),
    path('', views.home, name='home'),
    #path("monitoreo/real/", views.monitoreo_real, name="monitoreo_real"),
    #path("monitoreo/demo/", views.monitoreo_demo, name="monitoreo_demo"),
    path("api/demo/<uuid:viaje_id>/", views.api_ruta_demo, name="api_ruta_demo"),

    path('api/demo/registrar/', views.registrar_posicion_demo, name='registrar_posicion_demo'),

    #path('demo_viaje/', views.demo_viaje, name='demo_viaje'),


    # Autenticación
    # Autenticación: Usar next_page para forzar la redirección post-logout.
    path('login/', auth_views.LoginView.as_view(template_name='transporte/login.html'), name='login'),
    # ¡Línea Corregida!
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Registro
    path('registro/', views.registro, name='registro'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar'),



    # APIs usadas por el mapa
    #path('api/ruta/', views.obtener_ruta, name='api_ruta'),
    path('api/viajes_demo/', views.lista_viajes_demo, name='lista_viajes_demo'),

    path("panel_analitico/", views.panel_analitico, name="panel_analitico"),

    # EquiposGPs
    path("equipos/", views.equipos_list, name="equipos_list"),
    path("equipos/<int:pk>/", views.equipos_detalle, name="equipos_detalle"),
    path("equipos/crear/", views.equipos_crear, name="equipos_crear"),
    path("equipos/<int:pk>/editar/", views.equipos_editar, name="equipos_editar"),
    path("equipos/<int:pk>/eliminar/", views.equipos_eliminar, name="equipos_eliminar"),

    # Vehículos
    path('vehiculos/', views.vehiculo_list, name='vehiculo_list'),
    path('vehiculos/nuevo/', views.vehiculo_create, name='vehiculo_create'),
    path('vehiculos/<int:pk>/editar/', views.vehiculo_update, name='vehiculo_update'),
    path('vehiculos/<int:pk>/eliminar/', views.vehiculo_delete, name='vehiculo_delete'),

    # Viajes
    path('viajes/', views.viaje_list, name='viaje_list'),
    path('viajes/nuevo/', views.viaje_create, name='viaje_create'),
    path('viajes/<uuid:pk>/editar/', views.viaje_edit, name='viaje_edit'),
    path('viajes/<uuid:pk>/eliminar/', views.viaje_delete, name='viaje_delete'),
    path('viajes/<uuid:pk>/', views.viaje_detalle, name='viaje_detalle'),


    path('viaje/<uuid:viaje_id>/registros_api/', views.registros_api, name='registros_api'),
    path('viaje/<uuid:viaje_id>/monitor/', views.monitor_viaje, name='monitor_viaje'),

    path('viaje/<uuid:viaje_id>/actualizar_ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('viaje/<uuid:viaje_id>/actualizar_ubicacion_api/', views.actualizar_ubicacion_api, name='actualizar_ubicacion_api'),
    path('viaje/<uuid:viaje_id>/monitoreo/', views.monitoreo_viaje, name='monitoreo_viaje'),
    path('viaje/<uuid:viaje_id>/obtener_ubicaciones/', views.obtener_ubicaciones, name='obtener_ubicaciones'),
    path('viaje/<uuid:viaje_id>/demo/', views.demo_viaje, name='demo_viaje'),


    path("monitoreo/demo/", views.monitoreo_demo, name="monitoreo_demo"),
    path("api/ruta/", views.obtener_ruta, name="api_ruta"),

     # Reportes
    path("reportes/viajes-completados/", views.reporte_viajes_completados, name="reporte_viajes_completados"),


]
