from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone
from apps.usuarios.models import Usuario


MONEDAS_SOPORTADAS = [
    {'codigo': 'PYG', 'nombre': 'Guaraní Paraguayo', 'simbolo': 'Gs'},
    {'codigo': 'BRL', 'nombre': 'Real Brasileño', 'simbolo': 'R$'},
    {'codigo': 'USD', 'nombre': 'Dólar Americano', 'simbolo': 'US$'},
    {'codigo': 'ARS', 'nombre': 'Peso Argentino', 'simbolo': 'AR$'},
]

MONEDAS_VALIDAS = [m['codigo'] for m in MONEDAS_SOPORTADAS]


class TasaCambio(models.Model):
    """Tasa del día: 1 unidad de moneda extranjera = `tasa` Guaraníes.
    Se actualiza a diario (la tasa de frontera cambia seguido)."""
    moneda = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=50, blank=True, default='')
    simbolo = models.CharField(max_length=10, blank=True, default='')
    tasa = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Gs por 1 unidad'
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'caja_tasas_cambio'
        verbose_name = 'Tasa de Cambio'
        verbose_name_plural = 'Tasas de Cambio'

    def __str__(self):
        return f'{self.moneda}: 1 = {self.tasa} Gs'


def tasa_de(moneda):
    """Tasa vigente para una moneda. PYG siempre = 1.
    Devuelve 0 para monedas sin tasa configurada (no bloquea el cobro,
    se guarda el monto tal cual)."""
    if not moneda or moneda == 'PYG':
        return 1.0
    t = TasaCambio.objects.filter(moneda=moneda).first()
    return float(t.tasa) if t else 0.0


def obtener_tasas_cambio():
    """Devuelve {moneda: tasa} con PYG = 1, para cálculos y arqueos."""
    tasas = {t.moneda: float(t.tasa) for t in TasaCambio.objects.all()}
    tasas.setdefault('PYG', 1.0)
    return tasas


def convertir_a_pyg(monto, moneda, tasa=None):
    """Convierte un monto en moneda extranjera a guaraníes (redondeado a entero).
    Si la moneda es PYG (o no está definida) devuelve el monto tal cual."""
    monto = Decimal(str(monto or 0))
    if not moneda or moneda == 'PYG':
        return monto
    t = Decimal(str(tasa)) if tasa is not None else Decimal(str(tasa_de(moneda)))
    if not t:
        return Decimal('0')
    return (monto * t).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


class CajaSession(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cajero'
    )
    fondo_inicial = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Fondo Inicial Gs.')
    apertura_en = models.DateTimeField(auto_now_add=True, verbose_name='Apertura')
    cierre_en = models.DateTimeField(null=True, blank=True, verbose_name='Cierre')
    estado = models.CharField(
        max_length=20,
        choices=[('abierta', 'Abierta'), ('cerrada', 'Cerrada')],
        default='abierta'
    )
    notas_apertura = models.TextField(blank=True, default='')
    notas_cierre = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'caja_sesiones'
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'
        ordering = ['-apertura_en']

    def __str__(self):
        return f'Caja #{self.id} ({self.usuario.nombre if self.usuario else "?"}) - {self.apertura_en.strftime("%d/%m/%Y %H:%M")}'

    def cerrar(self):
        self.cierre_en = timezone.now()
        self.estado = 'cerrada'
        self.save()

    def total_ventas_efectivo(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='venta', metodo_pago='efectivo'
        )) or 0

    def total_ventas_tarjeta(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='venta', metodo_pago='tarjeta'
        )) or 0

    def total_ventas_transferencia(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='venta', metodo_pago='transferencia'
        )) or 0

    def total_ventas_qr(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='venta', metodo_pago='qr'
        )) or 0

    def total_ingresos_extra(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='ingreso_extra'
        )) or 0

    def total_retiros(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='retiro'
        )) or 0

    def total_propinas(self):
        return sum(float(m.propina) for m in self.movimientos.filter(
            tipo='venta'
        )) or 0

    def total_ventas(self):
        return sum(float(m.monto_pyg) for m in self.movimientos.filter(
            tipo='venta'
        )) or 0

    def efectivo_esperado(self):
        ventas_efectivo = self.total_ventas_efectivo()
        ingresos = self.total_ingresos_extra()
        retiros = self.total_retiros()
        return float(self.fondo_inicial) + ventas_efectivo + ingresos - retiros


class MovimientoCaja(models.Model):
    session = models.ForeignKey(
        CajaSession,
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('venta', 'Venta'),
            ('ingreso_extra', 'Ingreso Extra'),
            ('retiro', 'Retiro'),
            ('ajuste', 'Ajuste'),
        ],
        default='venta'
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('tarjeta', 'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('qr', 'QR'),
            ('mixto', 'Mixto'),
        ],
        default='efectivo'
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    moneda = models.CharField(max_length=10, default='PYG')
    monto_pyg = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Monto en Gs.')
    tasa_usada = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                     verbose_name='Tasa de cambio usada (Gs por 1 unidad)')
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimientos_caja'
    )
    detalle_pagos = models.JSONField(null=True, blank=True, verbose_name='Detalle de pagos mixtos')
    motivo = models.CharField(max_length=255, blank=True, default='',
                              verbose_name='Motivo (retiros/ingresos)')
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    propina = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Propina')
    vuelto = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Vuelto')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'caja_movimientos'
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_tipo_display()} {self.monto_pyg}Gs - {self.created_at.strftime("%H:%M")}'


class CorteCaja(models.Model):
    session = models.ForeignKey(
        CajaSession,
        on_delete=models.CASCADE,
        related_name='cortes'
    )
    usuario_cierre = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    fondo_inicial = models.DecimalField(max_digits=12, decimal_places=0)
    total_ventas_efectivo = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_ventas_tarjeta = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_ventas_transferencia = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_ventas_qr = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_ingresos_extra = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_retiros = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_propinas = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    # Arqueo
    denominaciones = models.JSONField(null=True, blank=True,
                                      verbose_name='Conteo de billetes/monedas')
    totales_por_moneda = models.JSONField(null=True, blank=True,
                                          verbose_name='Conteo físico por moneda')
    tasas_aplicadas = models.JSONField(null=True, blank=True,
                                       verbose_name='Tasas usadas en el arqueo')
    total_contado_efectivo = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                                  verbose_name='Efectivo contado físicamente')
    total_esperado = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    diferencia = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                      verbose_name='Diferencia (sobrante+/faltante-)')
    tipo_diferencia = models.CharField(max_length=20, blank=True, default='',
                                       choices=[('', 'Sin diferencia'), ('sobrante', 'Sobrante'),
                                                ('faltante', 'Faltante')])
    observaciones = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'caja_cortes'
        verbose_name = 'Corte de Caja'
        verbose_name_plural = 'Cortes de Caja'
        ordering = ['-created_at']

    def __str__(self):
        return f'Corte #{self.id} - {self.created_at.strftime("%d/%m/%Y %H:%M")}'
