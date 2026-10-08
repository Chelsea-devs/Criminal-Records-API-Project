from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from records.models import Criminal, Charge, Evidence, CaseNote


class Command(BaseCommand):
    help = "Create premium demonstration records and an admin account."

    def handle(self, *args, **options):
        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username="chelsea",
            defaults={
                "email": "admin@criminalapi.local",
                "first_name": "System",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Chelsea919!")
        admin.save()

        examples = [
            {
                "full_name": "Michael Adewale",
                "aliases": "The Broker",
                "gender": "male",
                "nationality": "Nigerian",
                "last_known_location": "Ikeja, Lagos",
                "risk_score": 82,
                "status": "wanted",
                "is_repeat_offender": True,
                "investigating_officer": "Inspector A. Bello",
                "summary": "Subject linked to multiple financial fraud investigations.",
                "charges": [
                    ("Financial Fraud", "Obtaining funds through false representation.", "high", "under_trial", "CR-2026-041", "250000.00"),
                    ("Identity Theft", "Use of another person's identity for fraudulent transactions.", "high", "pending", "CR-2026-052", "150000.00"),
                ],
            },
            {
                "full_name": "Sarah Okon",
                "aliases": "",
                "gender": "female",
                "nationality": "Nigerian",
                "last_known_location": "Abeokuta, Ogun State",
                "risk_score": 45,
                "status": "in_custody",
                "is_repeat_offender": False,
                "investigating_officer": "DSP M. Lawal",
                "summary": "Case under active investigation.",
                "charges": [
                    ("Property Damage", "Wilful destruction of private property.", "moderate", "pending", "OG-2026-018", "75000.00"),
                ],
            },
            {
                "full_name": "Daniel Musa",
                "aliases": "D-Money",
                "gender": "male",
                "nationality": "Nigerian",
                "last_known_location": "Abuja, FCT",
                "risk_score": 68,
                "status": "released",
                "is_repeat_offender": True,
                "investigating_officer": "Officer T. James",
                "summary": "Released pending further investigation.",
                "charges": [
                    ("Cybercrime", "Unauthorized access to protected computer systems.", "critical", "convicted", "FCT-2025-114", "500000.00"),
                ],
            },
        ]

        for data in examples:
            charges = data.pop("charges")
            criminal, _ = Criminal.objects.get_or_create(
                full_name=data["full_name"],
                defaults={**data, "created_by": admin},
            )
            for offence, description, severity, status, case_number, fine_amount in charges:
                charge, charge_created = Charge.objects.get_or_create(
                    criminal=criminal,
                    case_number=case_number,
                    defaults={
                        "offence": offence,
                        "description": description,
                        "severity": severity,
                        "status": status,
                        "date_charged": date.today() - timedelta(days=30),
                        "court_name": "State High Court",
                        "fine_amount": fine_amount,
                    },
                )
                if not charge_created and not charge.fine_amount:
                    charge.fine_amount = fine_amount
                    charge.save(update_fields=["fine_amount", "updated_at"])
            Evidence.objects.get_or_create(
                criminal=criminal,
                title="Primary case document",
                defaults={
                    "evidence_type": "document",
                    "description": "Verified case documentation.",
                    "storage_reference": f"EV-{criminal.criminal_id}",
                    "collected_by": data["investigating_officer"],
                    "verified": True,
                },
            )
            CaseNote.objects.get_or_create(
                criminal=criminal,
                title="Initial investigation note",
                defaults={
                    "body": "Record reviewed and assigned for continued investigation.",
                    "author": admin,
                    "confidential": False,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            "Demo records created. Login: chelsea / Chelsea919!"
        ))
