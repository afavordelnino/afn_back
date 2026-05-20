from django.urls import include, path
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.routers import DefaultRouter

from plataforma.views import (
    CategoriaRecetaViewSet,
    IngredienteViewSet,
    MenuSemanalViewSet,
    ProveedorViewSet,
    RecetaViewSet,
    SeccionAlmacenViewSet,
    SeccionSistemaViewSet,
    UnidadMedidaViewSet,
    UsuarioViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('unidades-medida', UnidadMedidaViewSet, basename='unidad-medida')
router.register('secciones-almacen', SeccionAlmacenViewSet, basename='seccion-almacen')
router.register('proveedores', ProveedorViewSet, basename='proveedor')
router.register('ingredientes', IngredienteViewSet, basename='ingrediente')
router.register('categorias-receta', CategoriaRecetaViewSet, basename='categoria-receta')
router.register('recetas', RecetaViewSet, basename='receta')
router.register('menus-semanales', MenuSemanalViewSet, basename='menu-semanal')
router.register('secciones-sistema', SeccionSistemaViewSet, basename='seccion-sistema')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
   path('auth/', ObtainAuthToken.as_view(), name='authenticate'),
   path('', include(router.urls)),
]
