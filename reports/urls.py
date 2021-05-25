from django.urls import path
from django.views.generic import RedirectView

from .views import report_view


app_name = "reports"

urlpatterns = [
    path("<slug:slug>/<uuid:cache_token>", report_view, name="report_view"),
    path("", RedirectView.as_view(url="/", permanent=True)),
]
