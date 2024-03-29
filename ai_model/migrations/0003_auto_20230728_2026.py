# Generated by Django 3.2.1 on 2023-07-28 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_model', '0002_captionkeyword_ocrkeyword_sttkeyword'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ocrresult',
            name='time',
            field=models.DecimalField(decimal_places=4, max_digits=20),
        ),
        migrations.AlterField(
            model_name='sttresult',
            name='end_time',
            field=models.DecimalField(decimal_places=4, max_digits=20),
        ),
        migrations.AlterField(
            model_name='sttresult',
            name='start_time',
            field=models.DecimalField(decimal_places=4, max_digits=20),
        ),
        migrations.AlterField(
            model_name='youtubecaption',
            name='end_time',
            field=models.DecimalField(decimal_places=4, max_digits=20),
        ),
        migrations.AlterField(
            model_name='youtubecaption',
            name='start_time',
            field=models.DecimalField(decimal_places=4, max_digits=20),
        ),
    ]
