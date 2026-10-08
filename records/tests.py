from decimal import Decimal
from urllib.request import urlopen

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .models import Criminal, Charge


class CriminalAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="officer", password="StrongPass123!", is_staff=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.criminal = Criminal.objects.create(
            full_name="Test Subject",
            gender="male",
            last_known_location="Lagos",
            risk_score=55,
            created_by=self.user,
        )
        self.charge = Charge.objects.create(
            criminal=self.criminal,
            offence="Test Offence",
            description="Test charge description",
            severity="high",
        )

    def test_list_contains_nested_charges(self):
        response = self.client.get("/api/v1/criminals/")
        self.assertEqual(response.status_code, 200)
        row = response.data["results"][0]
        self.assertEqual(row["charges"][0]["offence"], "Test Offence")

    def test_create_criminal_from_api(self):
        response = self.client.post("/api/v1/criminals/", {
            "full_name": "New Subject",
            "gender": "female",
            "last_known_location": "Abuja",
            "risk_score": 32,
            "status": "active",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["criminal_id"].startswith("CR-"))

    def test_create_criminal_with_charge_and_fine_from_api(self):
        response = self.client.post("/api/v1/criminals/", {
            "full_name": "Charge Subject",
            "gender": "female",
            "last_known_location": "Abuja",
            "risk_score": 61,
            "status": "active",
            "charge_offence": "Financial Fraud",
            "charge_description": "Fraudulent transfer under investigation.",
            "charge_severity": "high",
            "charge_status": "under_trial",
            "charge_case_number": "FCT-2026-014",
            "fine_amount": "175000.50",
        }, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        criminal = Criminal.objects.get(full_name="Charge Subject")
        charge = criminal.charges.get()
        self.assertEqual(charge.offence, "Financial Fraud")
        self.assertEqual(charge.case_number, "FCT-2026-014")
        self.assertEqual(charge.fine_amount, Decimal("175000.50"))
        self.assertEqual(response.data["total_fines"], "175000.50")
        self.assertEqual(response.data["charges"][0]["fine_amount"], "175000.50")

    def test_api_update_adds_another_charge_without_replacing_existing_charges(self):
        response = self.client.patch(
            f"/api/v1/criminals/{self.criminal.criminal_id}/",
            {
                "charge_offence": "Money Laundering",
                "charge_case_number": "LG-2026-208",
                "fine_amount": "85000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.criminal.charges.count(), 2)
        self.assertEqual(response.data["total_fines"], "85000.00")
        self.assertTrue(self.criminal.charges.filter(offence="Test Offence").exists())

    def test_api_rejects_fine_without_a_charge(self):
        response = self.client.post("/api/v1/criminals/", {
            "full_name": "Invalid Fine",
            "gender": "male",
            "last_known_location": "Lagos",
            "risk_score": 20,
            "status": "active",
            "fine_amount": "25000.00",
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("charge_offence", response.data)

    def test_api_rejects_negative_fine(self):
        response = self.client.post("/api/v1/criminals/", {
            "full_name": "Negative Fine",
            "gender": "male",
            "last_known_location": "Lagos",
            "risk_score": 20,
            "status": "active",
            "charge_offence": "Theft",
            "fine_amount": "-1.00",
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("fine_amount", response.data)

    def test_browsable_api_displays_charge_and_fine_fields(self):
        response = self.client.get("/api/v1/criminals/", HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="charge_offence"')
        self.assertContains(response, 'name="fine_amount"')
        self.assertContains(response, "Charges / offence")
        self.assertContains(response, "Fine amount (NGN)")

    def test_nested_charge_post(self):
        response = self.client.post(
            f"/api/v1/criminals/{self.criminal.criminal_id}/charges/",
            {
                "offence": "New Charge",
                "description": "Created through nested endpoint",
                "severity": "moderate",
                "status": "pending",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.criminal.charges.count(), 2)

    def test_update_and_delete_without_admin(self):
        response = self.client.patch(
            f"/api/v1/criminals/{self.criminal.criminal_id}/",
            {"status": "wanted"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(
            f"/api/v1/criminals/{self.criminal.criminal_id}/"
        )
        self.assertEqual(response.status_code, 204)


class CriminalChargeManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="manager", password="StrongPass123!", is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)

    def criminal_payload(self, **extra):
        return {
            "full_name": "Management Subject",
            "gender": "male",
            "last_known_location": "Lagos",
            "risk_score": "42",
            "status": "active",
            "charge_severity": "moderate",
            "charge_status": "pending",
            **extra,
        }

    def test_management_form_displays_charges_and_fine_section(self):
        response = self.client.get("/criminals/new/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Charges and fine")
        self.assertContains(response, 'name="charge_offence"')
        self.assertContains(response, 'name="fine_amount"')

    def test_management_form_creates_record_charge_and_fine_together(self):
        response = self.client.post("/criminals/new/", self.criminal_payload(
            charge_offence="Property Damage",
            charge_description="Damage to commercial property.",
            charge_case_number="LG-2026-445",
            fine_amount="65000.75",
        ))

        self.assertEqual(response.status_code, 302)
        criminal = Criminal.objects.get(full_name="Management Subject")
        charge = criminal.charges.get()
        self.assertEqual(charge.offence, "Property Damage")
        self.assertEqual(charge.fine_amount, Decimal("65000.75"))

    def test_management_form_rejects_fine_without_charge(self):
        response = self.client.post("/criminals/new/", self.criminal_payload(
            fine_amount="65000.00",
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a charge or offence")
        self.assertFalse(Criminal.objects.filter(full_name="Management Subject").exists())

    def test_directory_and_record_detail_show_total_fines(self):
        criminal = Criminal.objects.create(
            full_name="Management Subject", gender="male", last_known_location="Lagos"
        )
        Charge.objects.create(
            criminal=criminal,
            offence="Court Offence",
            description="Recorded legal offence.",
            fine_amount=Decimal("12345.67"),
        )

        self.assertEqual(criminal.get_absolute_url(), f"/criminals/{criminal.criminal_id}/")
        directory = self.client.get("/criminals/")
        detail = self.client.get(criminal.get_absolute_url())

        self.assertContains(directory, "Total fine")
        self.assertContains(directory, "12345.67")
        self.assertContains(detail, "Total fines")
        self.assertContains(detail, "12345.67")

    def test_django_admin_exposes_charge_fine_inline(self):
        response = self.client.get("/admin/records/criminal/add/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fine_amount")

    def test_seed_demo_populates_fine_amounts(self):
        call_command("seed_demo", verbosity=0)

        self.assertEqual(
            sum((charge.fine_amount for charge in Charge.objects.all()), Decimal("0.00")),
            Decimal("975000.00"),
        )


class InterfaceAssetTests(StaticLiveServerTestCase):
    def test_homepage_requests_versioned_premium_stylesheet(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/static/css/app.css?v=20260824')
        self.assertContains(response, 'class="hero"')

    def test_stylesheet_is_served_with_css_content_type(self):
        response = urlopen(f"{self.live_server_url}/static/css/app.css", timeout=5)

        self.assertEqual(response.status, 200)
        self.assertIn("text/css", response.headers["Content-Type"])
        stylesheet = response.read().decode("utf-8")
        self.assertIn("--teal:#167c77", stylesheet)
        self.assertIn("@media(max-width:1180px)", stylesheet)

    def test_menu_script_is_served(self):
        response = urlopen(f"{self.live_server_url}/static/js/app.js", timeout=5)

        self.assertEqual(response.status, 200)
