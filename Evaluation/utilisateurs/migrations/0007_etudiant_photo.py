# Generated by Django 5.0.2 on 2025-04-09 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0006_alter_etudiant_licence'),
    ]

    operations = [
        migrations.AddField(
            model_name='etudiant',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='photos_profil/'),
        ),
    ]
