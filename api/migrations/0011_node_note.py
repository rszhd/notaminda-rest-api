# Generated by Django 5.1.1 on 2024-10-01 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_delete_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='note',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
