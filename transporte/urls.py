from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('viajes/', views.viaje_list, name='viaje_list'),
    path('viaje/<uuid:viaje_id>/', views.viaje_detalle, name='viaje_detalle'),
    path('viaje/<uuid:viaje_id>/ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),


    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='transporte/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Registro
    path('registro/', views.registro, name='registro'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar'),

    path('viaje/nuevo/', views.viaje_crear, name='viaje_crear'),

]
