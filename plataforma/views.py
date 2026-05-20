import csv
import io
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import (
    CategoriaReceta,
    Ingrediente,
    MenuSemanal,
    MenuSemanalDetalle,
    MenuSemanalDetalleReceta,
    Proveedor,
    Receta,
    RecetaIngrediente,
    SeccionAlmacen,
    SeccionSistema,
    UnidadMedida,
    Usuario,
)
from .serializers import (
    CategoriaRecetaSerializer,
    IngredienteSerializer,
    MenuSemanalSerializer,
    ProveedorSerializer,
    RecetaIngredienteSerializer,
    RecetaSerializer,
    SeccionAlmacenSerializer,
    SeccionSistemaSerializer,
    UnidadMedidaSerializer,
    UsuarioSerializer,
)


class SeccionSistemaViewSet(viewsets.ModelViewSet):
    queryset = SeccionSistema.objects.all()
    serializer_class = SeccionSistemaSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.prefetch_related('secciones_acceso').all()
    serializer_class = UsuarioSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method.lower() == 'get':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer

    @action(detail=False, methods=['get'], url_path='plantilla')
    def plantilla(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="plantilla_unidades_medida.csv"'

        writer = csv.writer(response)
        writer.writerow(['clave', 'nombre', 'activo'])
        writer.writerow(['KG', 'Kilogramo', 'true'])
        writer.writerow(['LT', 'Litro', 'true'])
        writer.writerow(['PZ', 'Pieza', 'true'])
        return response

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='carga-masiva'
    )
    def carga_masiva(self, request):
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'detail': 'Debes adjuntar un archivo CSV en el campo archivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contenido = archivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {'detail': 'El archivo debe estar codificado en UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reader = csv.DictReader(io.StringIO(contenido))
        columnas_requeridas = {'clave', 'nombre', 'activo'}

        if not reader.fieldnames or not columnas_requeridas.issubset(set(reader.fieldnames)):
            return Response(
                {'detail': 'La plantilla debe incluir las columnas: clave, nombre, activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        creadas = 0
        actualizadas = 0
        errores = []

        for index, row in enumerate(reader, start=2):
            clave = (row.get('clave') or '').strip().upper()
            nombre = (row.get('nombre') or '').strip()
            activo = self._parse_bool(row.get('activo'))

            if not clave:
                errores.append({'fila': index, 'error': 'La clave es obligatoria.'})
                continue

            if len(clave) > 10:
                errores.append({'fila': index, 'error': 'La clave debe tener máximo 10 caracteres.'})
                continue

            if len(nombre) > 60:
                errores.append({'fila': index, 'error': 'El nombre debe tener máximo 60 caracteres.'})
                continue

            unidad, created = UnidadMedida.objects.update_or_create(
                clave=clave,
                defaults={
                    'nombre': nombre,
                    'activo': activo
                }
            )

            if created:
                creadas += 1
            else:
                actualizadas += 1

        return Response({
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores
        })

    def _parse_bool(self, value):
        normalized = str(value or '').strip().lower()
        return normalized in ['1', 'true', 'si', 'sí', 'yes', 'activo', 'activa']


class SeccionAlmacenViewSet(viewsets.ModelViewSet):
    queryset = SeccionAlmacen.objects.all()
    serializer_class = SeccionAlmacenSerializer

    @action(detail=False, methods=['get'], url_path='plantilla')
    def plantilla(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="plantilla_secciones_almacen.csv"'

        writer = csv.writer(response)
        writer.writerow(['nombre', 'activo'])
        writer.writerow(['SECO', 'true'])
        writer.writerow(['REFRIGERADO', 'true'])
        writer.writerow(['CONGELADO', 'true'])
        return response

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='carga-masiva'
    )
    def carga_masiva(self, request):
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'detail': 'Debes adjuntar un archivo CSV en el campo archivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contenido = archivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {'detail': 'El archivo debe estar codificado en UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reader = csv.DictReader(io.StringIO(contenido))
        columnas_requeridas = {'nombre', 'activo'}

        if not reader.fieldnames or not columnas_requeridas.issubset(set(reader.fieldnames)):
            return Response(
                {'detail': 'La plantilla debe incluir las columnas: nombre, activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        creadas = 0
        actualizadas = 0
        errores = []

        for index, row in enumerate(reader, start=2):
            nombre = (row.get('nombre') or '').strip().upper()
            activo = self._parse_bool(row.get('activo'))

            if not nombre:
                errores.append({'fila': index, 'error': 'El nombre es obligatorio.'})
                continue

            if len(nombre) > 80:
                errores.append({'fila': index, 'error': 'El nombre debe tener máximo 80 caracteres.'})
                continue

            seccion, created = SeccionAlmacen.objects.update_or_create(
                nombre=nombre,
                defaults={'activo': activo}
            )

            if created:
                creadas += 1
            else:
                actualizadas += 1

        return Response({
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores
        })

    def _parse_bool(self, value):
        normalized = str(value or '').strip().lower()
        return normalized in ['1', 'true', 'si', 'sí', 'yes', 'activo', 'activa']


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

    @action(detail=False, methods=['get'], url_path='plantilla')
    def plantilla(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="plantilla_proveedores.csv"'

        writer = csv.writer(response)
        writer.writerow(['nombre', 'activo'])
        writer.writerow(['A Favor del Niño', 'true'])
        writer.writerow(['Fundación del Dr. Simi', 'true'])
        writer.writerow(['Vegetales frescos', 'true'])
        return response

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='carga-masiva'
    )
    def carga_masiva(self, request):
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'detail': 'Debes adjuntar un archivo CSV en el campo archivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contenido = archivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {'detail': 'El archivo debe estar codificado en UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reader = csv.DictReader(io.StringIO(contenido))
        columnas_requeridas = {'nombre', 'activo'}

        if not reader.fieldnames or not columnas_requeridas.issubset(set(reader.fieldnames)):
            return Response(
                {'detail': 'La plantilla debe incluir las columnas: nombre, activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        creadas = 0
        actualizadas = 0
        errores = []

        for index, row in enumerate(reader, start=2):
            nombre = (row.get('nombre') or '').strip()
            activo = self._parse_bool(row.get('activo'))

            if not nombre:
                errores.append({'fila': index, 'error': 'El nombre es obligatorio.'})
                continue

            if len(nombre) > 180:
                errores.append({'fila': index, 'error': 'El nombre debe tener máximo 180 caracteres.'})
                continue

            proveedor, created = Proveedor.objects.update_or_create(
                nombre=nombre,
                defaults={'activo': activo}
            )

            if created:
                creadas += 1
            else:
                actualizadas += 1

        return Response({
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores
        })

    def _parse_bool(self, value):
        normalized = str(value or '').strip().lower()
        return normalized in ['1', 'true', 'si', 'sí', 'yes', 'activo', 'activa']


class IngredienteViewSet(viewsets.ModelViewSet):
    queryset = Ingrediente.objects.select_related(
        'unidad_compra',
        'seccion_almacen'
    ).prefetch_related(
        'proveedores__proveedor',
        'proveedores__precios'
    )
    serializer_class = IngredienteSerializer


class CategoriaRecetaViewSet(viewsets.ModelViewSet):
    queryset = CategoriaReceta.objects.all()
    serializer_class = CategoriaRecetaSerializer

    @action(detail=False, methods=['get'], url_path='plantilla')
    def plantilla(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="plantilla_categorias_receta.csv"'

        writer = csv.writer(response)
        writer.writerow(['nombre', 'activo'])
        writer.writerow(['Desayuno', 'true'])
        writer.writerow(['Colacion', 'true'])
        writer.writerow(['Plato fuerte', 'true'])
        return response

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='carga-masiva'
    )
    def carga_masiva(self, request):
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'detail': 'Debes adjuntar un archivo CSV en el campo archivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contenido = archivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {'detail': 'El archivo debe estar codificado en UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reader = csv.DictReader(io.StringIO(contenido))
        columnas_requeridas = {'nombre', 'activo'}

        if not reader.fieldnames or not columnas_requeridas.issubset(set(reader.fieldnames)):
            return Response(
                {'detail': 'La plantilla debe incluir las columnas: nombre, activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        creadas = 0
        actualizadas = 0
        errores = []

        for index, row in enumerate(reader, start=2):
            nombre = (row.get('nombre') or '').strip()
            activo = self._parse_bool(row.get('activo'))

            if not nombre:
                errores.append({'fila': index, 'error': 'El nombre es obligatorio.'})
                continue

            if len(nombre) > 80:
                errores.append({'fila': index, 'error': 'El nombre debe tener máximo 80 caracteres.'})
                continue

            categoria, created = CategoriaReceta.objects.update_or_create(
                nombre=nombre,
                defaults={'activo': activo}
            )

            if created:
                creadas += 1
            else:
                actualizadas += 1

        return Response({
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores
        })

    def _parse_bool(self, value):
        normalized = str(value or '').strip().lower()
        return normalized in ['1', 'true', 'si', 'sí', 'yes', 'activo', 'activa']


class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.select_related(
        'categoria_uso',
        'categoria_2'
    ).prefetch_related(
        'ingredientes__ingrediente',
        'ingredientes__unidad_medida'
    )
    serializer_class = RecetaSerializer

    @action(detail=True, methods=['post'], url_path='ingredientes', url_name='ingredientes-create')
    def ingredientes_create(self, request, pk=None):
        receta = self.get_object()
        serializer = RecetaIngredienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(receta=receta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path='ingredientes/(?P<ingrediente_id>[^/.]+)',
        url_name='ingrediente-detail'
    )
    def ingrediente_detail(self, request, pk=None, ingrediente_id=None):
        receta = self.get_object()
        ingrediente = get_object_or_404(RecetaIngrediente, pk=ingrediente_id, receta=receta)

        if request.method == 'DELETE':
            ingrediente.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = RecetaIngredienteSerializer(ingrediente, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MenuSemanalViewSet(viewsets.ModelViewSet):
    queryset = MenuSemanal.objects.prefetch_related(
        'detalles__tiempo_comida',
        'detalles__recetas__receta'
    )
    serializer_class = MenuSemanalSerializer

    @action(detail=True, methods=['post'], url_path='guardar-detalles')
    def guardar_detalles(self, request, pk=None):
        menu = self.get_object()
        detalles = request.data.get('detalles', [])

        if not isinstance(detalles, list):
            return Response(
                {'detail': 'El campo detalles debe ser una lista.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in detalles:
            receta_ids = self._parse_receta_ids(item.get('receta_ids', []))
            detalle, created = MenuSemanalDetalle.objects.update_or_create(
                menu=menu,
                fecha=item.get('fecha'),
                tiempo_comida_id=item.get('tiempo_comida'),
                defaults={
                    'dia_semana': item.get('dia_semana'),
                    'pax': item.get('pax') or 0,
                    'sin_servicio': bool(item.get('sin_servicio')),
                    'texto_original': item.get('texto_original') or '',
                    'notas': item.get('notas') or '',
                }
            )

            detalle.recetas.all().delete()

            if not detalle.sin_servicio:
                for index, receta_id in enumerate(receta_ids, start=1):
                    MenuSemanalDetalleReceta.objects.create(
                        detalle=detalle,
                        receta_id=receta_id,
                        orden=index,
                    )

        menu = self.get_queryset().get(pk=menu.pk)
        serializer = self.get_serializer(menu)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='imprimir')
    def imprimir(self, request, pk=None):
        menu = self.get_queryset().get(pk=pk)
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.35 * inch,
            leftMargin=0.35 * inch,
            topMargin=0.35 * inch,
            bottomMargin=0.35 * inch,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'MenuTitle',
            parent=styles['Title'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#243847'),
        )
        text_style = ParagraphStyle(
            'MenuText',
            parent=styles['BodyText'],
            fontSize=7,
            leading=9,
        )
        header_style = ParagraphStyle(
            'MenuHeader',
            parent=styles['BodyText'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=1,
        )

        story = [
            Paragraph(escape(menu.nombre or 'Menú semanal'), title_style),
            Paragraph(
                'Semana del %s al %s · Estado: %s' % (menu.fecha_inicio, menu.fecha_fin, menu.estado),
                styles['BodyText']
            ),
            Spacer(1, 0.15 * inch),
        ]

        days = self._menu_days(menu)
        categorias = self._menu_categories(menu)
        detalle_map = {
            (detalle.fecha.isoformat(), detalle.tiempo_comida_id): detalle
            for detalle in menu.detalles.all()
        }

        table_data = [[
            Paragraph('Tiempo / PAX', header_style),
            *[Paragraph('%s<br/>%s' % (day['nombre'], day['fecha']), header_style) for day in days],
        ]]

        for categoria in categorias:
            first_detail = next(
                (
                    detalle for detalle in menu.detalles.all()
                    if detalle.tiempo_comida_id == categoria.id
                ),
                None
            )
            pax = first_detail.pax if first_detail else 0
            row = [Paragraph('%s<br/>PAX: %s' % (escape(categoria.nombre), pax), text_style)]

            for day in days:
                detalle = detalle_map.get((day['fecha'], categoria.id))
                row.append(Paragraph(self._detalle_text(detalle), text_style))

            table_data.append(row)

        table = Table(
            table_data,
            colWidths=[1.25 * inch, 1.7 * inch, 1.7 * inch, 1.7 * inch, 1.7 * inch, 1.7 * inch],
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#76A6CC')),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#9FB7C9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F6F9FB')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

        document.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="menu_semanal_%s.pdf"' % menu.id
        return response

    def _parse_receta_ids(self, receta_ids):
        if not isinstance(receta_ids, list):
            return []

        parsed_ids = []

        for receta_id in receta_ids:
            try:
                parsed_id = int(receta_id)
            except (TypeError, ValueError):
                continue

            if parsed_id not in parsed_ids:
                parsed_ids.append(parsed_id)

        return parsed_ids

    def _menu_days(self, menu):
        day_names = {
            1: 'Lunes',
            2: 'Martes',
            3: 'Miércoles',
            4: 'Jueves',
            5: 'Viernes',
        }
        days = []

        for detalle in menu.detalles.all():
            item = {
                'fecha': detalle.fecha.isoformat(),
                'nombre': day_names.get(detalle.dia_semana, str(detalle.dia_semana)),
                'dia_semana': detalle.dia_semana,
            }

            if item not in days:
                days.append(item)

        return sorted(days, key=lambda item: item['dia_semana'])

    def _menu_categories(self, menu):
        categorias = []

        for detalle in menu.detalles.all():
            if detalle.tiempo_comida not in categorias:
                categorias.append(detalle.tiempo_comida)

        return sorted(categorias, key=lambda categoria: categoria.nombre)

    def _detalle_text(self, detalle):
        if not detalle:
            return ''

        if detalle.sin_servicio:
            return 'SIN SERVICIO'

        recetas = [
            escape(receta.receta.nombre)
            for receta in detalle.recetas.all()
        ]

        if recetas:
            return '<br/>'.join(recetas)

        return escape(detalle.texto_original or '')
