from django.urls import include, path
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.routers import DefaultRouter

from plataforma.views import (
    CategoriaProveedorViewSet,
    CategoriaRecetaViewSet,
    GrupoComensalesViewSet,
    IngredienteViewSet,
    InventarioInsumoViewSet,
    MermaViewSet,
    MenuSemanalViewSet,
    MovimientoInventarioViewSet,
    NivelGrupoViewSet,
    PaxTiempoComidaViewSet,
    PeriodoGrupoViewSet,
    ProveedorViewSet,
    RecetaViewSet,
    RecepcionInsumoViewSet,
    SeccionAlmacenViewSet,
    SeccionSistemaViewSet,
    TiempoComidaViewSet,
    UnidadMedidaViewSet,
    UsuarioViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('unidades-medida', UnidadMedidaViewSet, basename='unidad-medida')
router.register('secciones-almacen', SeccionAlmacenViewSet, basename='seccion-almacen')
router.register('proveedores', ProveedorViewSet, basename='proveedor')
router.register('ingredientes', IngredienteViewSet, basename='ingrediente')
router.register('recepciones-insumos', RecepcionInsumoViewSet, basename='recepcion-insumo')
router.register('inventario-insumos', InventarioInsumoViewSet, basename='inventario-insumo')
router.register('movimientos-inventario', MovimientoInventarioViewSet, basename='movimiento-inventario')
router.register('mermas', MermaViewSet, basename='merma')
router.register('categorias-proveedor', CategoriaProveedorViewSet, basename='categoria-proveedor')
router.register('categorias-receta', CategoriaRecetaViewSet, basename='categoria-receta')
router.register('recetas', RecetaViewSet, basename='receta')
router.register('menus-semanales', MenuSemanalViewSet, basename='menu-semanal')
router.register('niveles-grupo', NivelGrupoViewSet, basename='nivel-grupo')
router.register('periodos-grupo', PeriodoGrupoViewSet, basename='periodo-grupo')
router.register('tiempos-comida', TiempoComidaViewSet, basename='tiempo-comida')
router.register('grupos-comensales', GrupoComensalesViewSet, basename='grupo-comensales')
router.register('pax-tiempos-comida', PaxTiempoComidaViewSet, basename='pax-tiempo-comida')
router.register('secciones-sistema', SeccionSistemaViewSet, basename='seccion-sistema')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
   path('auth/', ObtainAuthToken.as_view(), name='authenticate'),
   path('', include(router.urls)),
]
