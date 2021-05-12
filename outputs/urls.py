from django.urls import path
from django.views.generic import RedirectView

from .views import output_view


app_name = "outputs"

urlpatterns = [
    path("<slug:slug>/<uuid:cache_token>", output_view, name="output_view"),
    path("", RedirectView.as_view(url="/", permanent=True)),
]
