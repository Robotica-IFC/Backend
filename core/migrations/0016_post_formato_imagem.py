from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0015_equipe_criador')]

    operations = [
        migrations.AddField(
            model_name='post',
            name='formato_imagem',
            field=models.CharField(
                max_length=12,
                choices=[('QUADRADO', 'Quadrado'), ('RETANGULAR', 'Retangular')],
                default='RETANGULAR',
            ),
        ),
    ]
