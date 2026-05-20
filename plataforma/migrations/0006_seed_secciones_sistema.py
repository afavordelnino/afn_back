from django.db import migrations


SECCIONES = [
    ('bienvenida', 'Inicio'),
    ('menus-semanales', 'Menú semanal'),
    ('recetas', 'Recetas'),
    ('ingredientes', 'Ingredientes'),
    ('proveedores', 'Proveedores'),
    ('secciones-almacen', 'Secciones de almacén'),
    ('categorias-receta', 'Categoría receta'),
    ('usuarios', 'Usuarios'),
    ('unidades-medida', 'Unidades de medida'),
]


def seed_secciones(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')

    for clave, nombre in SECCIONES:
        SeccionSistema.objects.update_or_create(
            clave=clave,
            defaults={
                'nombre': nombre,
                'activo': True,
            }
        )


def unseed_secciones(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.filter(
        clave__in=[clave for clave, nombre in SECCIONES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0005_seccionsistema_usuario_imagen_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_secciones, unseed_secciones),
    ]
