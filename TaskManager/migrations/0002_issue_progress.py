# Generated by Django 2.2 on 2019-05-05 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TaskManager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='progress',
            field=models.IntegerField(default=0),
        ),
    ]
