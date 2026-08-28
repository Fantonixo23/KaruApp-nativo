from django.db import models


class Configuracion(models.Model):
    nombre_empresa = models.CharField(max_length=255)
    ruc = models.CharField(max_length=20)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    tasa_iva = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    timbrado_numero = models.CharField(max_length=20, default='001-001-0000001')
    establecimiento = models.CharField(max_length=3, default='001')
    punto_expedicion = models.CharField(max_length=3, default='001')
    estado = models.CharField(
        max_length=20,
        choices=[
            ('demo', 'Demo'),
            ('activo', 'Activo'),
            ('suspendido', 'Suspendido')
        ],
        default='demo'
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    tamano_papel = models.CharField(
        max_length=4,
        choices=[('58mm', '58mm'), ('80mm', '80mm')],
        default='58mm',
        help_text='Tamaño de papel para impresión térmica'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'configuracion'
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'
    
    def __str__(self):
        return self.nombre_empresa


class Timbrado(models.Model):
    establecimiento = models.CharField(max_length=3, default='001')
    punto_expedicion = models.CharField(max_length=3, default='001')
    numero_inicio = models.IntegerField()
    numero_fin = models.IntegerField()
    numero_actual = models.IntegerField(default=0)
    fecha_vencimiento = models.DateField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'timbrados'
        verbose_name = 'Timbrado'
        verbose_name_plural = 'Timbrados'
    
    def __str__(self):
        return f"{self.establecimiento}-{self.punto_expedicion}"


class Factura(models.Model):
    numero = models.CharField(max_length=20)
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas'
    )
    ruc_cliente = models.CharField(max_length=20)
    nombre_cliente = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('borrador', 'Borrador'),
            ('generada', 'Generada'),
            ('anulada', 'Anulada')
        ],
        default='borrador'
    )
    total = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'facturas'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Factura {self.numero}"


class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    etiqueta = models.CharField(max_length=100)
    icono = models.CharField(max_length=50, default='payments')
    color = models.CharField(max_length=7, default='#4CAF50')
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = 'metodos_pago'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
        ordering = ['orden']

    def __str__(self):
        return self.etiqueta