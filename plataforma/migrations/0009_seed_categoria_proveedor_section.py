from django.db import migrations


def seed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.update_or_create(
        clave='categorias-proveedor',
        defaults={
            'nombre': 'Categorías proveedor',
            'activo': True,
        }
    )


def unseed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.filter(clave='categorias-proveedor').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0008_categoriaproveedor_proveedor_categorias_proveedor'),
    ]

    operations = [
        migrations.RunPython(seed_section, unseed_section),
    ]
