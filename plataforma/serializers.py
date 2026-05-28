from rest_framework import serializers

from .models import (
    CategoriaProveedor,
    CategoriaReceta,
    Ingrediente,
    IngredienteProveedor,
    GrupoComensales,
    GrupoTiempoComida,
    InventarioInsumo,
    Merma,
    MenuSemanal,
    MenuSemanalDetalle,
    MenuSemanalDetalleReceta,
    MovimientoInventario,
    NivelGrupo,
    PaxTiempoComida,
    PeriodoGrupo,
    PrecioIngredienteProveedor,
    Proveedor,
    Receta,
    RecetaIngrediente,
    RecepcionInsumo,
    RecepcionInsumoDetalle,
    SeccionAlmacen,
    SeccionSistema,
    TiempoComida,
    UnidadMedida,
    Usuario,
    recalcular_inventario_ingrediente,
)


class SeccionSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeccionSistema
        fields = ['id', 'clave', 'nombre', 'activo']


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    imagen_url = serializers.SerializerMethodField()
    secciones_acceso_detalle = SeccionSistemaSerializer(source='secciones_acceso', read_only=True, many=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'apellido_materno',
            'celular',
            'telefono',
            'tipo',
            'sexo',
            'is_active',
            'is_staff',
            'imagen',
            'imagen_url',
            'password',
            'secciones_acceso',
            'secciones_acceso_detalle',
        ]
        extra_kwargs = {
            'imagen': {'required': False},
            'secciones_acceso': {'required': False},
        }

    def get_imagen_url(self, obj):
        request = self.context.get('request')

        if not obj.imagen:
            return ''

        if request:
            return request.build_absolute_uri(obj.imagen.url)

        return obj.imagen.url

    def create(self, validated_data):
        password = validated_data.pop('password', '')
        secciones = validated_data.pop('secciones_acceso', [])
        user = Usuario(**validated_data)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        user.secciones_acceso.set(secciones)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        secciones = validated_data.pop('secciones_acceso', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if secciones is not None:
            instance.secciones_acceso.set(secciones)

        return instance


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = ['id', 'clave', 'nombre', 'activo']


class SeccionAlmacenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeccionAlmacen
        fields = ['id', 'nombre', 'activo']


class CategoriaProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProveedor
        fields = ['id', 'nombre', 'activo']


class ProveedorSerializer(serializers.ModelSerializer):
    categorias_proveedor_detalle = CategoriaProveedorSerializer(
        source='categorias_proveedor',
        read_only=True,
        many=True
    )

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'codigo_excel',
            'nombre',
            'contacto',
            'whatsapp',
            'email',
            'dias_entrega',
            'anticipacion_dias',
            'metodo_pedido',
            'categorias',
            'categorias_proveedor',
            'categorias_proveedor_detalle',
            'activo',
            'creado',
            'actualizado',
        ]
        read_only_fields = ['creado', 'actualizado']
        extra_kwargs = {
            'categorias_proveedor': {'required': False},
        }


class PrecioIngredienteProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioIngredienteProveedor
        fields = ['id', 'precio_unitario', 'fecha_precio', 'creado']


class IngredienteProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    precios = PrecioIngredienteProveedorSerializer(many=True, read_only=True)

    class Meta:
        model = IngredienteProveedor
        fields = [
            'id',
            'proveedor',
            'proveedor_nombre',
            'presentacion',
            'es_principal',
            'activo',
            'precios',
        ]


class IngredienteSerializer(serializers.ModelSerializer):
    unidad_compra_clave = serializers.CharField(source='unidad_compra.clave', read_only=True)
    seccion_almacen_nombre = serializers.CharField(source='seccion_almacen.nombre', read_only=True)
    proveedores = IngredienteProveedorSerializer(read_only=True, many=True)
    proveedores_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Ingrediente
        fields = [
            'id',
            'codigo_excel',
            'nombre',
            'unidad_compra',
            'unidad_compra_clave',
            'seccion_almacen',
            'seccion_almacen_nombre',
            'activo',
            'creado',
            'actualizado',
            'proveedores',
            'proveedores_ids',
        ]
        read_only_fields = ['creado', 'actualizado']

    def create(self, validated_data):
        proveedores_ids = validated_data.pop('proveedores_ids', [])
        ingrediente = super().create(validated_data)
        self._sync_proveedores(ingrediente, proveedores_ids)
        return ingrediente

    def update(self, instance, validated_data):
        proveedores_ids = validated_data.pop('proveedores_ids', None)
        ingrediente = super().update(instance, validated_data)

        if proveedores_ids is not None:
            self._sync_proveedores(ingrediente, proveedores_ids)

        return ingrediente

    def _sync_proveedores(self, ingrediente, proveedores_ids):
        proveedor_ids = set(proveedores_ids)

        IngredienteProveedor.objects.filter(
            ingrediente=ingrediente
        ).exclude(
            proveedor_id__in=proveedor_ids
        ).update(activo=False)

        for proveedor_id in proveedor_ids:
            IngredienteProveedor.objects.update_or_create(
                ingrediente=ingrediente,
                proveedor_id=proveedor_id,
                presentacion='',
                defaults={
                    'activo': True,
                    'es_principal': False,
                }
            )


class RecepcionInsumoDetalleSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source='ingrediente.nombre', read_only=True)
    unidad_medida_clave = serializers.CharField(source='unidad_medida.clave', read_only=True)
    precio_total = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)

    class Meta:
        model = RecepcionInsumoDetalle
        fields = [
            'id',
            'ingrediente',
            'ingrediente_nombre',
            'unidad_medida',
            'unidad_medida_clave',
            'cantidad',
            'precio_unitario',
            'precio_total',
            'notas',
        ]


class RecepcionInsumoSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    detalles = RecepcionInsumoDetalleSerializer(many=True)
    total_cantidad = serializers.SerializerMethodField()
    total_importe = serializers.SerializerMethodField()
    totales_por_unidad = serializers.SerializerMethodField()

    class Meta:
        model = RecepcionInsumo
        fields = [
            'id',
            'folio',
            'fecha',
            'proveedor',
            'proveedor_nombre',
            'notas',
            'creado',
            'actualizado',
            'detalles',
            'total_cantidad',
            'total_importe',
            'totales_por_unidad',
        ]
        read_only_fields = ['creado', 'actualizado']

    def get_total_cantidad(self, obj):
        return sum(detalle.cantidad for detalle in obj.detalles.all())

    def get_total_importe(self, obj):
        return sum(detalle.precio_total for detalle in obj.detalles.all())

    def get_totales_por_unidad(self, obj):
        totals = {}

        for detalle in obj.detalles.all():
            clave = detalle.unidad_medida.clave
            totals[clave] = totals.get(clave, 0) + detalle.cantidad

        return [
            {'unidad': unidad, 'cantidad': cantidad}
            for unidad, cantidad in totals.items()
        ]

    def create(self, validated_data):
        detalles = validated_data.pop('detalles', [])
        recepcion = RecepcionInsumo.objects.create(**validated_data)
        ingredientes = self._sync_detalles(recepcion, detalles)

        for ingrediente in ingredientes:
            recalcular_inventario_ingrediente(ingrediente)

        return recepcion

    def update(self, instance, validated_data):
        detalles = validated_data.pop('detalles', None)
        ingredientes = set(detalle.ingrediente for detalle in instance.detalles.all())

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if detalles is not None:
            instance.detalles.all().delete()
            ingredientes.update(self._sync_detalles(instance, detalles))

        for ingrediente in ingredientes:
            recalcular_inventario_ingrediente(ingrediente)

        return instance

    def _sync_detalles(self, recepcion, detalles):
        ingredientes = set()

        for detalle in detalles:
            ingrediente = detalle['ingrediente']
            detalle.setdefault('unidad_medida', ingrediente.unidad_compra)
            recepcion_detalle = RecepcionInsumoDetalle.objects.create(
                recepcion=recepcion,
                **detalle
            )
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.TIPO_ENTRADA_RECEPCION,
                fecha=recepcion.fecha,
                ingrediente=recepcion_detalle.ingrediente,
                unidad_medida=recepcion_detalle.unidad_medida,
                cantidad=recepcion_detalle.cantidad,
                precio_unitario=recepcion_detalle.precio_unitario,
                recepcion=recepcion,
                recepcion_detalle=recepcion_detalle,
                notas=recepcion_detalle.notas,
            )
            ingredientes.add(ingrediente)

        return ingredientes


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source='ingrediente.nombre', read_only=True)
    unidad_medida_clave = serializers.CharField(source='unidad_medida.clave', read_only=True)
    proveedor_nombre = serializers.CharField(source='recepcion.proveedor.nombre', read_only=True)
    folio_recepcion = serializers.CharField(source='recepcion.folio', read_only=True)
    merma_motivo = serializers.CharField(source='merma.motivo', read_only=True)
    precio_total = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id',
            'tipo',
            'fecha',
            'ingrediente',
            'ingrediente_nombre',
            'unidad_medida',
            'unidad_medida_clave',
            'cantidad',
            'precio_unitario',
            'precio_total',
            'recepcion',
            'folio_recepcion',
            'proveedor_nombre',
            'merma',
            'merma_motivo',
            'notas',
            'creado',
        ]
        read_only_fields = ['creado']


class InventarioInsumoSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source='ingrediente.nombre', read_only=True)
    ingrediente_codigo = serializers.CharField(source='ingrediente.codigo_excel', read_only=True)
    unidad_medida_clave = serializers.CharField(source='unidad_medida.clave', read_only=True)
    seccion_almacen_nombre = serializers.CharField(source='ingrediente.seccion_almacen.nombre', read_only=True)
    costo_promedio = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)
    movimientos = serializers.SerializerMethodField()

    class Meta:
        model = InventarioInsumo
        fields = [
            'id',
            'ingrediente',
            'ingrediente_nombre',
            'ingrediente_codigo',
            'unidad_medida',
            'unidad_medida_clave',
            'seccion_almacen_nombre',
            'cantidad_actual',
            'valor_total',
            'costo_promedio',
            'actualizado',
            'movimientos',
        ]

    def get_movimientos(self, obj):
        movimientos = MovimientoInventario.objects.filter(
            ingrediente=obj.ingrediente,
            unidad_medida=obj.unidad_medida
        ).select_related(
            'ingrediente',
            'unidad_medida',
            'recepcion',
            'recepcion__proveedor'
        )[:20]
        return MovimientoInventarioSerializer(movimientos, many=True).data


class MermaSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source='ingrediente.nombre', read_only=True)
    receta_nombre = serializers.CharField(source='receta.nombre', read_only=True)
    unidad_medida_clave = serializers.CharField(source='unidad_medida.clave', read_only=True)

    class Meta:
        model = Merma
        fields = [
            'id',
            'fecha',
            'tipo',
            'ingrediente',
            'ingrediente_nombre',
            'receta',
            'receta_nombre',
            'unidad_medida',
            'unidad_medida_clave',
            'cantidad',
            'regresa_inventario',
            'motivo',
            'notas',
            'creado',
            'actualizado',
        ]
        read_only_fields = ['creado', 'actualizado']

    def validate(self, attrs):
        tipo = attrs.get('tipo', getattr(self.instance, 'tipo', None))
        ingrediente = attrs.get('ingrediente', getattr(self.instance, 'ingrediente', None))
        receta = attrs.get('receta', getattr(self.instance, 'receta', None))

        if tipo == Merma.TIPO_INGREDIENTE and not ingrediente:
            raise serializers.ValidationError('Selecciona un ingrediente para registrar la merma.')

        if tipo == Merma.TIPO_RECETA and not receta:
            raise serializers.ValidationError('Selecciona una receta para registrar la merma.')

        return attrs

    def create(self, validated_data):
        merma = Merma.objects.create(**self._normalize(validated_data))
        self._sync_movimiento(merma)
        return merma

    def update(self, instance, validated_data):
        old_ingrediente = instance.ingrediente

        for attr, value in self._normalize(validated_data).items():
            setattr(instance, attr, value)

        instance.save()
        instance.movimientos_inventario.all().delete()
        self._sync_movimiento(instance)

        if old_ingrediente:
            recalcular_inventario_ingrediente(old_ingrediente)

        if instance.ingrediente:
            recalcular_inventario_ingrediente(instance.ingrediente)

        return instance

    def _normalize(self, data):
        tipo = data.get('tipo')

        if tipo == Merma.TIPO_INGREDIENTE:
            ingrediente = data.get('ingrediente')
            data['receta'] = None
            data['unidad_medida'] = data.get('unidad_medida') or ingrediente.unidad_compra
        elif tipo == Merma.TIPO_RECETA:
            data['ingrediente'] = None
            data['unidad_medida'] = None
            data['regresa_inventario'] = False

        return data

    def _sync_movimiento(self, merma):
        if merma.tipo != Merma.TIPO_INGREDIENTE or not merma.regresa_inventario:
            return

        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.TIPO_ENTRADA_REINTEGRO_MERMA,
            fecha=merma.fecha,
            ingrediente=merma.ingrediente,
            unidad_medida=merma.unidad_medida,
            cantidad=merma.cantidad,
            precio_unitario=0,
            merma=merma,
            notas=merma.motivo,
        )
        recalcular_inventario_ingrediente(merma.ingrediente)


class CategoriaRecetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaReceta
        fields = ['id', 'nombre', 'activo']


class NivelGrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NivelGrupo
        fields = ['id', 'nombre', 'activo']


class PeriodoGrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoGrupo
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'activo', 'notas', 'creado', 'actualizado']
        read_only_fields = ['creado', 'actualizado']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        activo = attrs.get('activo', getattr(self.instance, 'activo', True))

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError('La fecha fin no puede ser anterior a la fecha inicio.')

        if activo and fecha_inicio and fecha_fin:
            queryset = PeriodoGrupo.objects.filter(
                activo=True,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            )

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError('Ya existe un periodo activo que se traslapa con esas fechas.')

        return attrs


class TiempoComidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TiempoComida
        fields = ['id', 'clave', 'nombre', 'orden', 'activo']


class GrupoTiempoComidaSerializer(serializers.ModelSerializer):
    tiempo_comida_nombre = serializers.CharField(source='tiempo_comida.nombre', read_only=True)

    class Meta:
        model = GrupoTiempoComida
        fields = ['id', 'tiempo_comida', 'tiempo_comida_nombre', 'aplica', 'pax_override']


class GrupoComensalesSerializer(serializers.ModelSerializer):
    nivel_nombre = serializers.CharField(source='nivel.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    tiempos_comida = GrupoTiempoComidaSerializer(read_only=True, many=True)
    tiempos_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = GrupoComensales
        fields = [
            'id',
            'periodo',
            'periodo_nombre',
            'nombre',
            'nivel',
            'nivel_nombre',
            'alumnos',
            'activo',
            'tiempos_comida',
            'tiempos_config',
        ]

    def create(self, validated_data):
        tiempos_config = validated_data.pop('tiempos_config', [])
        grupo = super().create(validated_data)
        self._sync_tiempos(grupo, tiempos_config)
        return grupo

    def update(self, instance, validated_data):
        tiempos_config = validated_data.pop('tiempos_config', None)
        grupo = super().update(instance, validated_data)

        if tiempos_config is not None:
            self._sync_tiempos(grupo, tiempos_config)

        return grupo

    def _sync_tiempos(self, grupo, tiempos_config):
        current_ids = []

        for item in tiempos_config:
            tiempo_comida_id = item.get('tiempo_comida')

            if not tiempo_comida_id:
                continue

            current_ids.append(tiempo_comida_id)
            GrupoTiempoComida.objects.update_or_create(
                grupo=grupo,
                tiempo_comida_id=tiempo_comida_id,
                defaults={
                    'aplica': bool(item.get('aplica')),
                    'pax_override': item.get('pax_override') or None,
                }
            )

        if current_ids:
            GrupoTiempoComida.objects.filter(grupo=grupo).exclude(
                tiempo_comida_id__in=current_ids
            ).delete()


class PaxTiempoComidaSerializer(serializers.ModelSerializer):
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    tiempo_comida_nombre = serializers.CharField(source='tiempo_comida.nombre', read_only=True)

    class Meta:
        model = PaxTiempoComida
        fields = [
            'id',
            'periodo',
            'periodo_nombre',
            'tiempo_comida',
            'tiempo_comida_nombre',
            'pax_calculado',
            'pax_confirmado',
            'notas',
            'actualizado',
        ]
        read_only_fields = ['actualizado']


class RecetaIngredienteSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source='ingrediente.nombre', read_only=True)
    unidad_medida_clave = serializers.CharField(source='unidad_medida.clave', read_only=True)

    class Meta:
        model = RecetaIngrediente
        fields = [
            'id',
            'ingrediente',
            'ingrediente_nombre',
            'cantidad',
            'unidad_medida',
            'unidad_medida_clave',
            'notas',
            'activo',
        ]


class RecetaSerializer(serializers.ModelSerializer):
    categoria_uso_nombre = serializers.CharField(source='categoria_uso.nombre', read_only=True)
    categoria_2_nombre = serializers.CharField(source='categoria_2.nombre', read_only=True)
    ingredientes = RecetaIngredienteSerializer(read_only=True, many=True)

    class Meta:
        model = Receta
        fields = [
            'id',
            'codigo_excel',
            'nombre',
            'categoria_uso',
            'categoria_uso_nombre',
            'categoria_2',
            'categoria_2_nombre',
            'activo',
            'porciones_base',
            'kcal_porcion',
            'proteina_g',
            'lipidos_g',
            'hdc_g',
            'notas',
            'validado_nutri',
            'creado',
            'actualizado',
            'ingredientes',
        ]
        read_only_fields = ['creado', 'actualizado']


class MenuSemanalDetalleRecetaSerializer(serializers.ModelSerializer):
    receta_nombre = serializers.CharField(source='receta.nombre', read_only=True)

    class Meta:
        model = MenuSemanalDetalleReceta
        fields = ['id', 'receta', 'receta_nombre', 'orden', 'texto_original']


class MenuSemanalDetalleSerializer(serializers.ModelSerializer):
    tiempo_comida_nombre = serializers.CharField(source='tiempo_comida.nombre', read_only=True)
    recetas = MenuSemanalDetalleRecetaSerializer(read_only=True, many=True)

    class Meta:
        model = MenuSemanalDetalle
        fields = [
            'id',
            'menu',
            'fecha',
            'dia_semana',
            'tiempo_comida',
            'tiempo_comida_nombre',
            'pax',
            'sin_servicio',
            'texto_original',
            'notas',
            'recetas',
        ]


class MenuSemanalSerializer(serializers.ModelSerializer):
    detalles = MenuSemanalDetalleSerializer(read_only=True, many=True)

    class Meta:
        model = MenuSemanal
        fields = [
            'id',
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'activo',
            'notas',
            'creado',
            'actualizado',
            'detalles',
        ]
        read_only_fields = ['creado', 'actualizado']
