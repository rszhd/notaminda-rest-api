# Generated by Django 5.1.1 on 2024-10-07 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_mindmap_id_alter_node_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='title',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
