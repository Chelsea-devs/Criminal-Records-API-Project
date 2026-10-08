# Criminal Record Intelligence System — Charges and Fines Edition

This build includes direct charge and fine entry when creating or updating criminal records in the browsable API, the premium management interface and Django Admin. It also preserves the repaired dark-and-teal interface, reliable static assets and complete migrations.

## New capabilities

- Add an offence, description, severity, legal status, case number and naira fine directly when creating a criminal record.
- Add another charge and its fine while editing an existing criminal record.
- Use the same charge and fine fields on the browsable API, the premium criminal form and Django Admin.
- View total fines on the criminal directory, API responses, command dashboard and downloadable PDF reports.
- Prevent negative fines and reject fine details that are submitted without an offence.
- Criminal profile links now open the premium record page instead of accidentally opening the raw API response.
- Mugshot image upload instead of relying on an external photo URL.
- Evidence-file upload for documents, images, audio, video and digital evidence.
- Google Maps link for every last-known location.
- Administrative audit log showing create, update, delete and PDF-export activity.
- Dark command dashboard for authorized administrators.
- January-to-December yearly record analysis chart.
- Downloadable PDF report for each criminal record.
- Table-based homepage record display.
- Charge editing and all management controls available from the normal staff interface.
- Ordinary viewers cannot access the Django REST Framework backend, Django Admin, dashboard or editing forms.
- Logout now returns to the homepage and clears the authenticated session.

## Install and run

Use Python 3.13 or a compatible Python version:

```powershell
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:DJANGO_DEBUG="true"
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

The project intentionally does not include an old virtual environment or database. Run the commands above after extracting the ZIP so Django creates a clean database and applies every migration. You can also double-click `run_windows.bat`.

If your browser still displays an older cached page, press `Ctrl + Shift + R` once. The stylesheet should be available at `http://127.0.0.1:8000/static/css/app.css`.


The login page does not display these credentials.

## Adding charges and fines

Sign in as the administrator, then open `/api/v1/criminals/` or `/criminals/new/`. Complete the criminal identity fields and fill in **Charges / offence** and **Fine amount (NGN)**. Charge description, severity, status and case number are also available. Saving creates the criminal record and its linked charge together. Editing a criminal record with new charge details adds another linked charge without removing existing charges.

## Important pages

- Public homepage: `/`
- Public record directory: `/criminals/`
- Authorized command dashboard: `/dashboard/`
- Authorized Django Admin: `/admin/`
- Authorized private API: `/api/v1/`

The private API requires an authenticated staff account. Ordinary viewers receive an authorization error and are not shown links to backend services.

## Upload storage

Uploaded mugshots and evidence files are saved under the `media/` directory during local development. Back up this directory together with the database.

## PDF reports

Authorized staff can open a criminal record and click **Download PDF**. The report includes identity information, status, risk assessment, case summary, charges and evidence register.

## Security note

This is a development system handling highly sensitive information. Before real deployment, use HTTPS, PostgreSQL, secure file storage, malware scanning for uploaded files, role-specific permissions, encrypted backups and legal/privacy review.

## Case file search

Open `http://127.0.0.1:8000/case-files/search/` to search by case number, criminal ID, name, alias or offence.
