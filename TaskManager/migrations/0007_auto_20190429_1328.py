# Generated by Django 2.2 on 2019-04-29 13:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TaskManager', '0006_auto_20190429_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='TaskManager.UserProfile'),
        ),
    ]