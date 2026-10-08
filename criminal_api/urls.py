from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from records import api_views, views

router = DefaultRouter()
router.register("criminals", api_views.CriminalViewSet, basename="api-criminal")
router.register("charges", api_views.ChargeViewSet, basename="charge")
router.register("evidence", api_views.EvidenceViewSet, basename="evidence")
router.register("notes", api_views.CaseNoteViewSet, basename="case-note")

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("criminals/", views.criminal_list, name="criminal-list"),
    path("case-files/search/", views.case_file_search, name="case-file-search"),
    path("criminals/new/", views.criminal_create, name="criminal-create"),
    path("criminals/<str:criminal_id>/", views.criminal_detail, name="criminal-detail"),
    path("criminals/<str:criminal_id>/edit/", views.criminal_update, name="criminal-update"),
    path("criminals/<str:criminal_id>/delete/", views.criminal_delete, name="criminal-delete"),
    path("criminals/<str:criminal_id>/report.pdf", views.criminal_pdf, name="criminal-pdf"),
    path("criminals/<str:criminal_id>/charges/new/", views.charge_create, name="charge-create"),
    path("charges/<int:pk>/edit/", views.charge_update, name="charge-update"),
    path("charges/<int:pk>/delete/", views.charge_delete, name="charge-delete"),
    path("criminals/<str:criminal_id>/evidence/new/", views.evidence_create, name="evidence-create"),
    path("criminals/<str:criminal_id>/notes/new/", views.note_create, name="note-create"),

    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("api/v1/", include(router.urls)),
    path("api/v1/auth/token/", obtain_auth_token, name="api-token"),
    path("api/v1/statistics/", api_views.statistics, name="api-statistics"),
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    # Keep the premium interface available even when Django's staticfiles
    # development handler is bypassed or a previously missing asset is cached.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
