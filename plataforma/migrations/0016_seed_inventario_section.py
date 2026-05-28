from django.db import migrations


def seed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.update_or_create(
        clave='inventario-insumos',
        defaults={
            'nombre': 'Inventario',
            'activo': True,
        }
    )


def unseed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.filter(clave='inventario-insumos').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0015_movimientoinventario_inventarioinsumo'),
    ]

    operations = [
        migrations.RunPython(seed_section, unseed_section),
    ]
