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


class Proveedor(models.Model):
    nombre = models.CharField(max_length=180, unique=True)
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


class CategoriaReceta(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categoria_receta'
        ordering = ['nombre']


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
