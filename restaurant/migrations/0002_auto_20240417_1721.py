# Generated by Django 5.0.2 on 2024-04-17 15:16

from django.db import migrations

def create_tables(apps, schema_editor):
    Table = apps.get_model('restaurant', 'Table')
    for i in range(1, 101):  # 创建100张桌子
        Table.objects.create(name=f"Table {i}")

class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_tables),
    ]