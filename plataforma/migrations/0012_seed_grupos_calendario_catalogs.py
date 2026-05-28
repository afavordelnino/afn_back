from django.db import migrations


NIVELES = [
    'Inicial',
    'Preescolar',
    'Primaria',
    'Secundaria',
    'Administrativo',
]

TIEMPOS = [
    ('DESAYUNO', 'Desayuno', 1),
    ('COL_MAT', 'Colación Matutina', 2),
    ('COMIDA', 'Comida', 3),
    ('COL_VES', 'Colación Vespertina', 4),
]


def seed_catalogs(apps, schema_editor):
    NivelGrupo = apps.get_model('plataforma', 'NivelGrupo')
    TiempoComida = apps.get_model('plataforma', 'TiempoComida')

    for nombre in NIVELES:
        NivelGrupo.objects.update_or_create(
            nombre=nombre,
            defaults={'activo': True}
        )

    for clave, nombre, orden in TIEMPOS:
        TiempoComida.objects.update_or_create(
            clave=clave,
            defaults={
                'nombre': nombre,
                'orden': orden,
                'activo': True,
            }
        )


def unseed_catalogs(apps, schema_editor):
    NivelGrupo = apps.get_model('plataforma', 'NivelGrupo')
    TiempoComida = apps.get_model('plataforma', 'TiempoComida')
    NivelGrupo.objects.filter(nombre__in=NIVELES).delete()
    TiempoComida.objects.filter(clave__in=[clave for clave, nombre, orden in TIEMPOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0011_nivelgrupo_tiempocomida_periodogrupo_grupocomensales_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalogs, unseed_catalogs),
    ]
