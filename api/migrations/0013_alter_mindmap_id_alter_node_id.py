# Generated by Django 5.1.1 on 2024-10-02 12:15

import api.models.mindmap
import api.models.node
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_mindmap_is_private_alter_node_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mindmap',
            name='id',
            field=models.CharField(default=api.models.mindmap.generate_unique_id, editable=False, max_length=20, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='node',
            name='id',
            field=models.CharField(default=api.models.node.generate_unique_id, editable=False, max_length=30, primary_key=True, serialize=False),
        ),
    ]
