from django.urls import path
from .views import (
    lista_reservas,
    crear_reserva,
    modificar_reserva,
    cambiar_estado_reserva,
    eliminar_reserva,
)

urlpatterns = [
    path('reservas', lista_reservas, name='lista_reservas'),
    path('reservas/crear', crear_reserva, name='crear_reserva'),
    path('reservas/<int:pk>/editar', modificar_reserva, name='modificar_reserva'),
    path('reservas/<int:pk>/estado', cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('reservas/<int:pk>/eliminar', eliminar_reserva, name='eliminar_reserva'),
]