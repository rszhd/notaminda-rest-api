# Generated by Django 5.1.1 on 2024-10-02 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_node_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='mindmap',
            name='is_private',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='note',
            field=models.TextField(blank=True, default=''),
        ),
    ]
