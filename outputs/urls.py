from django.urls import path

from .views import output_view


app_name = "outputs"

urlpatterns = [
    path("<slug:slug>", output_view, name="output_view"),
]
