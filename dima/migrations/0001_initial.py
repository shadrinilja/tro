# Generated by Django 3.1.7 on 2022-12-31 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrgDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=350, verbose_name='название')),
                ('id_ogr', models.IntegerField(null=True, verbose_name='id организации')),
                ('inn', models.BigIntegerField(null=True, verbose_name='инн организации')),
                ('actual_year', models.IntegerField(null=True, verbose_name='актуальный год')),
                ('url_pars', models.URLField(null=True, verbose_name='урл_для парсинга')),
                ('publishDate', models.BigIntegerField(null=True, verbose_name='время публикации')),
            ],
        ),
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_doc', models.URLField(null=True, verbose_name='Ссылка на актуальный документ')),
                ('update_date', models.DateField(null=True)),
                ('trun', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pep', to='dima.orgdate')),
            ],
            options={
                'ordering': ['url_doc'],
                'unique_together': {('trun', 'update_date')},
            },
        ),
    ]