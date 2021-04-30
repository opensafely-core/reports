import structlog
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from social_django.utils import load_backend, load_strategy
from social_django.views import complete

from .github import get_html
from .models import Organisation, Output


logger = structlog.getLogger()


def landing(request):
    return render(request, "gateway/landing.html")


@never_cache
@csrf_exempt
def nhsid_complete(request, *args, **kwargs):
    """
    Return the complete view with expected arguments.

    A successful authentication from  NHS ID returns to /auth. social_django expects to
    find the backend name in the url (by default /complete/<backend>)
    """
    backend = "nhsid"
    uri = reverse("gateway:nhsid_complete")
    request.social_strategy = load_strategy(request)
    request.backend = load_backend(request.social_strategy, backend, uri)
    completed = complete(request, backend, *args, **kwargs)
    logger.info(
        "User logged in", user_id=request.user.pk, username=request.user.username
    )
    return completed


class OrganisationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View details for a single organisation.

    Permission is denied if the user is not a member of the requested organisation.
    """

    template_name = "gateway/organisation_detail.html"
    model = Organisation

    def test_func(self):
        """Check if the user is a member of the organisation"""
        organisation = self.get_object()
        return self.request.user.organisations.filter(id=organisation.id).exists()

    def get_object(self, queryset=None):
        return get_object_or_404(Organisation, code=self.kwargs["org_code"])


@cache_page(86400)
def output_view(request, slug):
    """
    Fetches the html output from github, and renders the style and body tags within the
    the output template page.  Caches for 24 hours.
    """
    output = get_object_or_404(Output, slug=slug)
    extracted = get_html(output)
    return TemplateResponse(
        request,
        "gateway/output.html",
        {"notebook_style": extracted["style"], "contents": extracted["body"]},
    )
