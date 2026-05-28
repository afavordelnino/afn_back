from django.db import migrations


def seed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.update_or_create(
        clave='recepcion-insumos',
        defaults={
            'nombre': 'Recepción de insumos',
            'activo': True,
        }
    )


def unseed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.filter(clave='recepcion-insumos').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0013_recepcioninsumo_recepcioninsumodetalle'),
    ]

    operations = [
        migrations.RunPython(seed_section, unseed_section),
    ]
