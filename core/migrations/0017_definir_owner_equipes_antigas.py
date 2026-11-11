from django.db import migrations


def definir_owners(apps, schema_editor):
    Equipe = apps.get_model('core', 'Equipe')
    vinculos = Equipe.professores.through
    database = schema_editor.connection.alias
    for equipe in Equipe.objects.using(database).filter(criador__isnull=True).iterator():
        professor_id = (vinculos.objects.using(database).filter(equipe_id=equipe.pk)
                        .order_by('pk').values_list('professor_id', flat=True).first())
        if professor_id:
            Equipe.objects.using(database).filter(pk=equipe.pk, criador__isnull=True).update(criador_id=professor_id)


class Migration(migrations.Migration):
    dependencies = [('core', '0016_post_formato_imagem')]

    operations = [migrations.RunPython(definir_owners, migrations.RunPython.noop)]
