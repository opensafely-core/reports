from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import OrganisationDetailView, landing, nhsid_complete

app_name = "gateway"

urlpatterns = [
    path("auth/", nhsid_complete, name="nhsid_complete"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "organisation/<str:org_code>",
        OrganisationDetailView.as_view(),
        name="organisation_detail",
    ),
    path("", landing, name="landing"),
]
