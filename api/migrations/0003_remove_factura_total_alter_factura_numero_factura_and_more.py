# Generated by Django 4.2.23 on 2025-07-29 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_trabajo_num_pedido_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='factura',
            name='total',
        ),
        migrations.AlterField(
            model_name='factura',
            name='numero_factura',
            field=models.CharField(editable=False, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='proforma',
            name='numero_proforma',
            field=models.CharField(editable=False, max_length=100, unique=True),
        ),
    ]
