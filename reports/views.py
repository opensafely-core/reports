import datetime

import structlog
from django.db.models import F, Q, Value
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from .github import GithubReport
from .job_server import JobServerReport
from .models import Report


logger = structlog.getLogger()


@never_cache
def landing(request):
    """Landing page for main site and post-login.  Displays recent Report activity"""
    # We want the ten most recently published or updated outputs, without duplication. Until we've pulled them all
    # back and compared their activity dates we don't know which ones we will be using, so we grab ten of each which
    # must be enough.
    all_reports = Report.objects.for_user(request.user).exclude(
        category__name__iexact="archive"
    )

    # To avoid duplication of reports in the activity list, we don't display the publication event for reports that
    # have subsequently been updated. However if they are updated on the same day that they were published then we
    # just consider that as a single publication event. The sum total of this is that we are only interested in
    # publication dates where there has been no update or where the update date is the same as publication.
    published = (
        all_reports.filter(
            Q(last_updated__isnull=True) | Q(publication_date__exact=F("last_updated")),
        )
        .order_by("-publication_date")[:10]
        .annotate(activity=Value("published"), activity_date=F("publication_date"))
    )

    # As above, we ignore updates when they happen on the same day as publication.
    updated = (
        all_reports.filter(
            last_updated__isnull=False,
            last_updated__gt=F("publication_date"),
        )
        .order_by("-last_updated")[:10]
        .annotate(activity=Value("updated"), activity_date=F("last_updated"))
    )

    # Merge the publish and update events and grab the ten most recent.
    recent_activity = sorted(
        [*published, *updated], key=lambda x: x.activity_date, reverse=True
    )[:10]
    context = {
        "recent_activity": recent_activity,
        "today": datetime.datetime.now(datetime.UTC).date(),
    }
    return render(request, "landing.html", context)


@never_cache
def report_view(request, slug):
    """
    Fetches an html report file from github, and renders the style and body tags within
    the report template page.  This entire view is never cached, however the template content is cached (in the template)
    for 24 hours using the report's cache_token as a key, and can be forced to refetch and update the cache with the
    `force-update` query parameter.
    """
    try:
        report = Report.objects.for_user(request.user).get(slug=slug)
    except Report.DoesNotExist:
        raise Http404("Report matching query does not exist")

    if "force-update" in request.GET:
        # Force an update by refreshing the cache_token and redirecting
        report.refresh_cache_token()
        logger.info(
            "Cache token refreshed and requests cache cleared; redirecting...",
            report_id=report.pk,
            slug=report.slug,
        )
        return redirect(report.get_absolute_url())

    remote_cls = GithubReport if report.uses_github else JobServerReport
    remote = remote_cls(report)

    return TemplateResponse(
        request,
        "report.html",
        {
            "remote": remote,
            "report": report,
        },
    )
