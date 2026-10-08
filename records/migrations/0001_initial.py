from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Criminal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("criminal_id", models.CharField(db_index=True, editable=False, max_length=24, unique=True)),
                ("full_name", models.CharField(db_index=True, max_length=150)),
                ("aliases", models.CharField(blank=True, max_length=255)),
                ("gender", models.CharField(choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], max_length=20)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("nationality", models.CharField(blank=True, max_length=80)),
                ("phone_number", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("last_known_location", models.CharField(db_index=True, max_length=255)),
                ("residential_address", models.TextField(blank=True)),
                ("occupation", models.CharField(blank=True, max_length=120)),
                ("identification_number", models.CharField(blank=True, max_length=100)),
                ("photo_url", models.URLField(blank=True)),
                ("risk_score", models.PositiveSmallIntegerField(default=20, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("status", models.CharField(choices=[("active", "Active"), ("wanted", "Wanted"), ("in_custody", "In Custody"), ("released", "Released"), ("closed", "Case Closed")], db_index=True, default="active", max_length=20)),
                ("is_repeat_offender", models.BooleanField(default=False)),
                ("arrest_date", models.DateField(blank=True, null=True)),
                ("release_date", models.DateField(blank=True, null=True)),
                ("investigating_officer", models.CharField(blank=True, max_length=150)),
                ("summary", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_criminal_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Charge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("offence", models.CharField(db_index=True, max_length=180)),
                ("offence_code", models.CharField(blank=True, max_length=60)),
                ("description", models.TextField()),
                ("severity", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("critical", "Critical")], default="moderate", max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("under_trial", "Under Trial"), ("convicted", "Convicted"), ("acquitted", "Acquitted"), ("dismissed", "Dismissed")], default="pending", max_length=20)),
                ("date_committed", models.DateField(blank=True, null=True)),
                ("date_charged", models.DateField(blank=True, null=True)),
                ("court_name", models.CharField(blank=True, max_length=180)),
                ("case_number", models.CharField(blank=True, db_index=True, max_length=100)),
                ("sentence", models.TextField(blank=True)),
                ("fine_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("prison_term_months", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("criminal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="charges", to="records.criminal")),
            ],
            options={"ordering": ["-date_charged", "-created_at"]},
        ),
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("evidence_type", models.CharField(choices=[("document", "Document"), ("image", "Image"), ("video", "Video"), ("audio", "Audio"), ("physical", "Physical"), ("digital", "Digital"), ("other", "Other")], max_length=20)),
                ("description", models.TextField(blank=True)),
                ("reference_url", models.URLField(blank=True)),
                ("storage_reference", models.CharField(blank=True, max_length=180)),
                ("collected_by", models.CharField(blank=True, max_length=150)),
                ("collected_at", models.DateTimeField(blank=True, null=True)),
                ("verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("charge", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="evidence_items", to="records.charge")),
                ("criminal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence_items", to="records.criminal")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CaseNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("body", models.TextField()),
                ("confidential", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("criminal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="case_notes", to="records.criminal")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="criminal",
            index=models.Index(fields=["full_name", "status"], name="records_cri_full_na_5f9046_idx"),
        ),
        migrations.AddIndex(
            model_name="criminal",
            index=models.Index(fields=["last_known_location"], name="records_cri_last_kn_7d80f2_idx"),
        ),
    ]
