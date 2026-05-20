from rest_framework import serializers

from .models import (
    CategoriaReceta,
    Ingrediente,
    IngredienteProveedor,
    MenuSemanal,
    MenuSemanalDetalle,
    MenuSemanalDetalleReceta,
    PrecioIngredienteProveedor,
    Proveedor,
    Receta,
    RecetaIngrediente,
    SeccionAlmacen,
    SeccionSistema,
    UnidadMedida,
    Usuario,
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


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'activo', 'creado', 'actualizado']
        read_only_fields = ['creado', 'actualizado']


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


class CategoriaRecetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaReceta
        fields = ['id', 'nombre', 'activo']


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
