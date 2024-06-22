# Generated by Django 5.0 on 2024-02-03 01:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assignments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="IDClientCounter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RenameField(
            model_name="proxyreport",
            old_name="connected_users",
            new_name="connected_clients",
        ),
        migrations.RemoveField(
            model_name="proxy",
            name="description",
        ),
        migrations.AddField(
            model_name="client",
            name="latitude",
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name="client",
            name="longitude",
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name="proxy",
            name="capacity",
            field=models.IntegerField(default=40),
        ),
        migrations.AddField(
            model_name="proxy",
            name="ip",
            field=models.CharField(default="0.0.0.0", max_length=30),
        ),
        migrations.AddField(
            model_name="proxy",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="proxy",
            name="latitude",
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name="proxy",
            name="longitude",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="proxy",
            name="is_blocked",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="proxy",
            name="url",
            field=models.CharField(max_length=100, null=True),
        ),
    ]