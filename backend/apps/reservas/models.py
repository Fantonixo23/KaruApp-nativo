from django.db import models


class Reserva(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_show', 'No asistió'),
    ]
    ESTADOS_ACTIVOS = ['pendiente', 'confirmada']

    mesa = models.ForeignKey('mesas.Mesa', on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_min = models.IntegerField(default=120)
    cliente_nombre = models.CharField(max_length=150)
    cliente_telefono = models.CharField(max_length=30, blank=True, null=True)
    comensales = models.IntegerField(default=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    nota = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['fecha', 'hora']

    def __str__(self):
        return f"{self.cliente_nombre} - Mesa {self.mesa.numero} ({self.fecha} {self.hora.strftime('%H:%M')})"

    @property
    def activa(self):
        return self.estado in self.ESTADOS_ACTIVOS

    @classmethod
    def vigentes_ahora(cls, **filtros):
        """Devuelve las reservas activas que están hoy dentro de su ventana de tiempo actual.
        Ventana = desde 30 min antes de la hora reservada hasta el fin del bloque
        (inicio + duracion) + 30 min de margen."""
        from django.utils import timezone
        now = timezone.localtime()
        hoy = now.date()
        actual_min = now.hour * 60 + now.minute
        qs = cls.objects.filter(
            fecha=hoy,
            estado__in=cls.ESTADOS_ACTIVOS,
            **filtros,
        ).select_related('mesa')
        return [r for r in qs if r.ventana_inicio <= actual_min <= r.ventana_fin]

    @property
    def ventana_inicio(self):
        """Minutos desde medianoche de la fecha: desde 30 min antes de la hora."""
        return max(0, (self.hora.hour * 60 + self.hora.minute) - 30)

    @property
    def ventana_fin(self):
        """Minutos desde medianoche de la fecha: inicio del bloque + duración + 30 min."""
        return (self.hora.hour * 60 + self.hora.minute) + self.duracion_min + 30

    @property
    def vigente_ahora(self):
        from django.utils import timezone
        now = timezone.localtime()
        if self.fecha != now.date():
            return False
        minutos = now.hour * 60 + now.minute
        return self.ventana_inicio <= minutos <= self.ventana_fin