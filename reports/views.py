import structlog
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from .github import GithubReport
from .job_server import JobServerReport
from .models import Report


logger = structlog.getLogger()


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
        "reports/report.html",
        {
            "remote": remote,
            "report": report,
        },
    )
