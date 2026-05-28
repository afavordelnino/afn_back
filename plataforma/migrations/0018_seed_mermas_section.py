from django.db import migrations


def seed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.update_or_create(
        clave='mermas',
        defaults={
            'nombre': 'Mermas',
            'activo': True,
        }
    )


def unseed_section(apps, schema_editor):
    SeccionSistema = apps.get_model('plataforma', 'SeccionSistema')
    SeccionSistema.objects.filter(clave='mermas').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0017_alter_movimientoinventario_tipo_merma_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_section, unseed_section),
    ]
