from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('viajes/', views.viaje_list, name='viaje_list'),
    path('viaje/<uuid:viaje_id>/', views.viaje_detalle, name='viaje_detalle'),
    #path('viaje/<uuid:viaje_id>/ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('viaje/nuevo/', views.viaje_crear, name='viaje_crear'),
    path('viaje/<uuid:viaje_id>/registros_api/', views.registros_api, name='registros_api'),
    path('viaje/<uuid:viaje_id>/monitor/', views.monitor_viaje, name='monitor_viaje'),


    path('viaje/<uuid:viaje_id>/actualizar_ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('viaje/<uuid:viaje_id>/actualizar_ubicacion_api/', views.actualizar_ubicacion_api, name='actualizar_ubicacion_api'),
    path('viaje/<uuid:viaje_id>/monitoreo/', views.monitoreo_viaje, name='monitoreo_viaje'),
    path('viaje/<uuid:viaje_id>/obtener_ubicaciones/', views.obtener_ubicaciones, name='obtener_ubicaciones'),
    path('viaje/<uuid:viaje_id>/demo/', views.demo_viaje, name='demo_viaje'),

    path("monitoreo/real/", views.monitoreo_real, name="monitoreo_real"),
    path("monitoreo/demo/", views.monitoreo_demo, name="monitoreo_demo"),
    path("api/demo/<uuid:viaje_id>/", views.api_ruta_demo, name="api_ruta_demo"),


    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='transporte/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Registro
    path('registro/', views.registro, name='registro'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar'),


]
