# Generated by Django 4.2 on 2023-05-28 12:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_model', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='youtubeurl',
            name='length',
        ),
        migrations.RemoveField(
            model_name='youtubeurl',
            name='title',
        ),
        migrations.CreateModel(
            name='YouTubeInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='YouTube Title', max_length=50)),
                ('length', models.IntegerField(help_text='YouTube Length')),
                ('url_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ai_model.youtubeurl')),
            ],
        ),
    ]
