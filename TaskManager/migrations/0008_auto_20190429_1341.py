# Generated by Django 2.2 on 2019-04-29 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TaskManager', '0007_auto_20190429_1328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='id',
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=30, primary_key=True, serialize=False),
        ),
    ]