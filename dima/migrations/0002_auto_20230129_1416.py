# Generated by Django 3.1.7 on 2023-01-29 11:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dima', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='doc',
            options={'ordering': ['url_doc', '-id']},
        ),
    ]