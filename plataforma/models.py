from django.db import models
from django.contrib.auth.models import  AbstractUser
import uuid


class Usuario(AbstractUser):
    fecha_inscripcion = models.DateField(auto_now_add=True, null=True, blank=True)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.IntegerField(default=1)
    celular = models.CharField(max_length=15,default="", blank=True, null=True)
    sexo = models.IntegerField(default=1)
    telefono = models.CharField(max_length=15,default="", blank=True, null=True)
    imagen = models.ImageField(max_length=160, upload_to="usuarios/", blank=True, null=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    secciones_acceso = models.ManyToManyField(
        'SeccionSistema',
        blank=True,
        related_name='usuarios'
    )
   

    @property
    def usuario_id(self):
        return self.id
    def __str__(self):
        return '%s %d' %(self.email, self.id)
    class Meta:
        db_table = 'usuario'


class SeccionSistema(models.Model):
    clave = models.CharField(max_length=60, unique=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'seccion_sistema'
        ordering = ['nombre']


class UnidadMedida(models.Model):
    clave = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=60, blank=True, default="")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.clave

    class Meta:
        db_table = 'unidad_medida'
        ordering = ['clave']


class SeccionAlmacen(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'seccion_almacen'
        ordering = ['nombre']


class CategoriaProveedor(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categoria_proveedor'
        ordering = ['nombre']


class Proveedor(models.Model):
    codigo_excel = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    nombre = models.CharField(max_length=180, unique=True)
    contacto = models.CharField(max_length=180, blank=True, default="")
    whatsapp = models.CharField(max_length=80, blank=True, default="")
    email = models.EmailField(max_length=180, blank=True, default="")
    dias_entrega = models.CharField(max_length=220, blank=True, default="")
    anticipacion_dias = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    metodo_pedido = models.CharField(max_length=80, blank=True, default="")
    categorias = models.TextField(blank=True, default="")
    categorias_proveedor = models.ManyToManyField(
        CategoriaProveedor,
        blank=True,
        related_name='proveedores'
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'proveedor'
        ordering = ['nombre']


class Ingrediente(models.Model):
    codigo_excel = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    nombre = models.CharField(max_length=220)
    unidad_compra = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='ingredientes'
    )
    seccion_almacen = models.ForeignKey(
        SeccionAlmacen,
        on_delete=models.PROTECT,
        related_name='ingredientes'
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'ingrediente'
        ordering = ['nombre']


class IngredienteProveedor(models.Model):
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name='proveedores'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='ingredientes'
    )
    presentacion = models.CharField(max_length=160, blank=True, default="")
    es_principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s - %s' % (self.ingrediente, self.proveedor)

    class Meta:
        db_table = 'ingrediente_proveedor'
        ordering = ['ingrediente__nombre', 'proveedor__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['ingrediente', 'proveedor', 'presentacion'],
                name='unique_ingrediente_proveedor_presentacion'
            )
        ]


class PrecioIngredienteProveedor(models.Model):
    ingrediente_proveedor = models.ForeignKey(
        IngredienteProveedor,
        on_delete=models.CASCADE,
        related_name='precios'
    )
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    fecha_precio = models.DateField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - $%s' % (self.ingrediente_proveedor, self.precio_unitario)

    class Meta:
        db_table = 'precio_ingrediente_proveedor'
        ordering = ['-fecha_precio', '-creado']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name='precio_ingrediente_proveedor_no_negativo'
            )
        ]


class RecepcionInsumo(models.Model):
    folio = models.CharField(max_length=40, blank=True, default="")
    fecha = models.DateField()
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='recepciones',
        blank=True,
        null=True
    )
    notas = models.TextField(blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.folio or 'Recepción %s' % self.fecha

    class Meta:
        db_table = 'recepcion_insumo'
        ordering = ['-fecha', '-creado']


class RecepcionInsumoDetalle(models.Model):
    recepcion = models.ForeignKey(
        RecepcionInsumo,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='recepciones'
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='recepciones_insumo'
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    notas = models.CharField(max_length=220, blank=True, default="")

    @property
    def precio_total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return '%s - %s' % (self.recepcion, self.ingrediente)

    class Meta:
        db_table = 'recepcion_insumo_detalle'
        ordering = ['ingrediente__nombre']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='recepcion_insumo_detalle_cantidad_positiva'
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name='recepcion_insumo_detalle_precio_no_negativo'
            ),
        ]


class InventarioInsumo(models.Model):
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name='inventarios'
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='inventarios_insumo'
    )
    cantidad_actual = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    valor_total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    actualizado = models.DateTimeField(auto_now=True)

    @property
    def costo_promedio(self):
        if not self.cantidad_actual:
            return 0

        return self.valor_total / self.cantidad_actual

    def __str__(self):
        return '%s - %s %s' % (self.ingrediente, self.cantidad_actual, self.unidad_medida)

    class Meta:
        db_table = 'inventario_insumo'
        ordering = ['ingrediente__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['ingrediente', 'unidad_medida'],
                name='unique_inventario_insumo_unidad'
            )
        ]


class MovimientoInventario(models.Model):
    TIPO_ENTRADA_RECEPCION = 'ENTRADA_RECEPCION'
    TIPO_ENTRADA_REINTEGRO_MERMA = 'ENTRADA_REINTEGRO_MERMA'
    TIPO_CHOICES = [
        (TIPO_ENTRADA_RECEPCION, 'Entrada por recepción'),
        (TIPO_ENTRADA_REINTEGRO_MERMA, 'Entrada por reintegro de merma'),
    ]

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default=TIPO_ENTRADA_RECEPCION)
    fecha = models.DateField()
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario'
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario'
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    recepcion = models.ForeignKey(
        RecepcionInsumo,
        on_delete=models.CASCADE,
        related_name='movimientos_inventario',
        blank=True,
        null=True
    )
    recepcion_detalle = models.ForeignKey(
        RecepcionInsumoDetalle,
        on_delete=models.CASCADE,
        related_name='movimientos_inventario',
        blank=True,
        null=True
    )
    merma = models.ForeignKey(
        'Merma',
        on_delete=models.CASCADE,
        related_name='movimientos_inventario',
        blank=True,
        null=True
    )
    notas = models.CharField(max_length=220, blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)

    @property
    def precio_total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return '%s - %s - %s' % (self.fecha, self.ingrediente, self.cantidad)

    class Meta:
        db_table = 'movimiento_inventario'
        ordering = ['-fecha', '-creado']


class Merma(models.Model):
    TIPO_INGREDIENTE = 'INGREDIENTE'
    TIPO_RECETA = 'RECETA'
    TIPO_CHOICES = [
        (TIPO_INGREDIENTE, 'Ingrediente'),
        (TIPO_RECETA, 'Receta'),
    ]

    fecha = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='mermas',
        blank=True,
        null=True
    )
    receta = models.ForeignKey(
        'Receta',
        on_delete=models.PROTECT,
        related_name='mermas',
        blank=True,
        null=True
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='mermas',
        blank=True,
        null=True
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    regresa_inventario = models.BooleanField(default=False)
    motivo = models.CharField(max_length=180, blank=True, default="")
    notas = models.TextField(blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s - %s' % (self.fecha, self.tipo)

    class Meta:
        db_table = 'merma'
        ordering = ['-fecha', '-creado']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='merma_cantidad_positiva'
            )
        ]


def recalcular_inventario_ingrediente(ingrediente):
    movimientos = MovimientoInventario.objects.filter(ingrediente=ingrediente).select_related('unidad_medida')
    totales = {}

    for movimiento in movimientos:
        unidad_id = movimiento.unidad_medida_id

        if unidad_id not in totales:
            totales[unidad_id] = {
                'cantidad': 0,
                'valor': 0,
                'unidad': movimiento.unidad_medida,
            }

        totales[unidad_id]['cantidad'] += movimiento.cantidad
        totales[unidad_id]['valor'] += movimiento.precio_total

    InventarioInsumo.objects.filter(ingrediente=ingrediente).delete()

    for total in totales.values():
        InventarioInsumo.objects.create(
            ingrediente=ingrediente,
            unidad_medida=total['unidad'],
            cantidad_actual=total['cantidad'],
            valor_total=total['valor'],
        )


class CategoriaReceta(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categoria_receta'
        ordering = ['nombre']


class NivelGrupo(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'nivel_grupo'
        ordering = ['nombre']


class PeriodoGrupo(models.Model):
    nombre = models.CharField(max_length=120)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'periodo_grupo'
        ordering = ['-fecha_inicio']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='periodo_grupo_fechas_validas'
            )
        ]


class TiempoComida(models.Model):
    clave = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    orden = models.PositiveSmallIntegerField(default=1)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'tiempo_comida'
        ordering = ['orden', 'nombre']


class GrupoComensales(models.Model):
    periodo = models.ForeignKey(
        PeriodoGrupo,
        on_delete=models.CASCADE,
        related_name='grupos'
    )
    nombre = models.CharField(max_length=100)
    nivel = models.ForeignKey(
        NivelGrupo,
        on_delete=models.PROTECT,
        related_name='grupos'
    )
    alumnos = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return '%s - %s' % (self.periodo, self.nombre)

    class Meta:
        db_table = 'grupo_comensales'
        ordering = ['periodo__fecha_inicio', 'nivel__nombre', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['periodo', 'nombre'],
                name='unique_grupo_comensales_periodo_nombre'
            )
        ]


class GrupoTiempoComida(models.Model):
    grupo = models.ForeignKey(
        GrupoComensales,
        on_delete=models.CASCADE,
        related_name='tiempos_comida'
    )
    tiempo_comida = models.ForeignKey(
        TiempoComida,
        on_delete=models.PROTECT,
        related_name='grupos'
    )
    aplica = models.BooleanField(default=True)
    pax_override = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return '%s - %s' % (self.grupo, self.tiempo_comida)

    class Meta:
        db_table = 'grupo_tiempo_comida'
        ordering = ['grupo__nombre', 'tiempo_comida__orden']
        constraints = [
            models.UniqueConstraint(
                fields=['grupo', 'tiempo_comida'],
                name='unique_grupo_tiempo_comida'
            )
        ]


class PaxTiempoComida(models.Model):
    periodo = models.ForeignKey(
        PeriodoGrupo,
        on_delete=models.CASCADE,
        related_name='pax_tiempos'
    )
    tiempo_comida = models.ForeignKey(
        TiempoComida,
        on_delete=models.PROTECT,
        related_name='pax_periodos'
    )
    pax_calculado = models.PositiveIntegerField(default=0)
    pax_confirmado = models.PositiveIntegerField(blank=True, null=True)
    notas = models.TextField(blank=True, default="")
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s - %s' % (self.periodo, self.tiempo_comida)

    class Meta:
        db_table = 'pax_tiempo_comida'
        ordering = ['periodo__fecha_inicio', 'tiempo_comida__orden']
        constraints = [
            models.UniqueConstraint(
                fields=['periodo', 'tiempo_comida'],
                name='unique_pax_tiempo_comida_periodo'
            )
        ]


class Receta(models.Model):
    codigo_excel = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    nombre = models.CharField(max_length=220)
    categoria_uso = models.ForeignKey(
        CategoriaReceta,
        on_delete=models.PROTECT,
        related_name='recetas_uso'
    )
    categoria_2 = models.ForeignKey(
        CategoriaReceta,
        on_delete=models.PROTECT,
        related_name='recetas_secundarias',
        blank=True,
        null=True
    )
    activo = models.BooleanField(default=True)
    porciones_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    kcal_porcion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proteina_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lipidos_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hdc_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True, default="")
    validado_nutri = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'receta'
        ordering = ['nombre']


class RecetaIngrediente(models.Model):
    receta = models.ForeignKey(
        Receta,
        on_delete=models.CASCADE,
        related_name='ingredientes'
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='recetas'
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name='recetas_ingredientes'
    )
    notas = models.CharField(max_length=220, blank=True, default="")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return '%s - %s' % (self.receta, self.ingrediente)

    class Meta:
        db_table = 'receta_ingrediente'
        ordering = ['receta__nombre', 'ingrediente__nombre']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='receta_ingrediente_cantidad_positiva'
            )
        ]


class MenuSemanal(models.Model):
    ESTADO_BORRADOR = 'BORRADOR'
    ESTADO_ACTIVO = 'ACTIVO'
    ESTADO_CERRADO = 'CERRADO'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_CERRADO, 'Cerrado'),
    ]

    nombre = models.CharField(max_length=120, blank=True, default="")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre or '%s al %s' % (self.fecha_inicio, self.fecha_fin)

    class Meta:
        db_table = 'menu_semanal'
        ordering = ['-fecha_inicio']


class MenuSemanalDetalle(models.Model):
    DIA_LUNES = 1
    DIA_MARTES = 2
    DIA_MIERCOLES = 3
    DIA_JUEVES = 4
    DIA_VIERNES = 5
    DIA_CHOICES = [
        (DIA_LUNES, 'Lunes'),
        (DIA_MARTES, 'Martes'),
        (DIA_MIERCOLES, 'Miércoles'),
        (DIA_JUEVES, 'Jueves'),
        (DIA_VIERNES, 'Viernes'),
    ]

    menu = models.ForeignKey(
        MenuSemanal,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    fecha = models.DateField()
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    tiempo_comida = models.ForeignKey(
        CategoriaReceta,
        on_delete=models.PROTECT,
        related_name='menus_detalle'
    )
    pax = models.PositiveIntegerField(default=0)
    sin_servicio = models.BooleanField(default=False)
    texto_original = models.CharField(max_length=260, blank=True, default="")
    notas = models.CharField(max_length=260, blank=True, default="")

    def __str__(self):
        return '%s - %s - %s' % (self.menu, self.fecha, self.tiempo_comida)

    class Meta:
        db_table = 'menu_semanal_detalle'
        ordering = ['fecha', 'tiempo_comida__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['menu', 'fecha', 'tiempo_comida'],
                name='unique_menu_fecha_tiempo_comida'
            )
        ]


class MenuSemanalDetalleReceta(models.Model):
    detalle = models.ForeignKey(
        MenuSemanalDetalle,
        on_delete=models.CASCADE,
        related_name='recetas'
    )
    receta = models.ForeignKey(
        Receta,
        on_delete=models.PROTECT,
        related_name='menus_detalle'
    )
    orden = models.PositiveIntegerField(default=1)
    texto_original = models.CharField(max_length=220, blank=True, default="")

    def __str__(self):
        return '%s - %s' % (self.detalle, self.receta)

    class Meta:
        db_table = 'menu_semanal_detalle_receta'
        ordering = ['orden']
        constraints = [
            models.UniqueConstraint(
                fields=['detalle', 'receta', 'orden'],
                name='unique_menu_detalle_receta_orden'
            )
        ]
