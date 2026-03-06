from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gradebook", "0002_alter_examimport_payload"),
    ]

    operations = [
        migrations.AddField(
            model_name="exam",
            name="identity_key",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="exam",
            name="identity_label",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
