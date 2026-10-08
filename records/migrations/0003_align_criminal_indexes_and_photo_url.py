from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0002_uploads_auditlog"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="criminal",
            new_name="records_cri_full_na_8b1891_idx",
            old_name="records_cri_full_na_5f9046_idx",
        ),
        migrations.RenameIndex(
            model_name="criminal",
            new_name="records_cri_last_kn_b59eec_idx",
            old_name="records_cri_last_kn_7d80f2_idx",
        ),
        migrations.AlterField(
            model_name="criminal",
            name="photo_url",
            field=models.URLField(
                blank=True,
                help_text="Legacy external photo URL (optional)",
            ),
        ),
    ]
