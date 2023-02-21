"""reports URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import RedirectView

from .forms import ReportsAuthenticationForm
from .views import landing, report_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        LoginView.as_view(
            template_name="login.html",
            authentication_form=ReportsAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("reports/", RedirectView.as_view(url="/", permanent=True)),
    path("reports/<slug:slug>/", report_view, name="report_view"),
    path("", landing, name="landing"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "OpenSAFELY Reports Admin"
