from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import landing, nhsid_complete

app_name = "gateway"

urlpatterns = [
    path("auth/", nhsid_complete, name="nhsid_complete"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", landing, name="landing"),
]
