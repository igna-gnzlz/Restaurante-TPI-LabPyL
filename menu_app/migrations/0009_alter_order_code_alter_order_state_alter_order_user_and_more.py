import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu_app', '0008_remove_product_slug_order_booking'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='code',
            field=models.CharField(blank=True, max_length=15, unique=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='state',
            field=models.CharField(choices=[('S', 'Solicitado por cliente'), ('P', 'Preparación'), ('E', 'Enviado'), ('R', 'Recibido'), ('C', 'Cancelado')], default='S', max_length=15),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='ordercontainsproduct',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='menu_app.product'),
        ),
    ]
