from datetime import datetime

import structlog
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, Value
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from social_django.utils import load_backend, load_strategy
from social_django.views import complete

from reports.models import Report

from .models import Organisation


logger = structlog.getLogger()


@never_cache
def landing(request):
    """Landing page for main site and post-login.  Displays recent Report activity"""
    # Find the latest 10 publication dates in reverse order; this is the maximum number of
    # Outputs with publication date that we'll show
    all_reports = Report.objects.for_user(request.user)
    published = all_reports.order_by("-publication_date")[:10].annotate(
        activity=Value("published"), activity_date=F("publication_date")
    )
    # Find the latest 10 last_updated dates in reverse order that are greater than
    # publication date; if published and output date are the same, we don't want to
    # show both; last updated should always be after published
    last_10_updated = all_reports.filter(
        last_updated__isnull=False,
        last_updated__gt=F("publication_date"),
    ).order_by("-last_updated")[:10]
    updated = last_10_updated.annotate(
        activity=Value("updated"), activity_date=F("last_updated")
    )
    # sort Outputs by activity date and select the 10 most recent; this may return
    # duplicate Outputs if their published and last_updated dates are both recent, but
    # that's OK
    recent_activity = sorted(
        [*published, *updated], key=lambda x: x.activity_date, reverse=True
    )[:10]
    context = {
        "recent_activity": recent_activity,
        "today": datetime.utcnow().date(),
    }
    return render(request, "gateway/landing.html", context)


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
