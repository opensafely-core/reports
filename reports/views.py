import structlog
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from lxml.html.clean import Cleaner

from .github import GithubReport
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

    github_report = GithubReport(report)
    return TemplateResponse(
        request,
        "reports/report.html",
        {
            "notebook_contents": process_html(github_report),
            "report": github_report.report,
            "repo_url": github_report.repo.url,
        },
    )


def process_html(github_report):
    # Fetch the processed html from the cache if available
    cache_key = str(github_report.report.cache_token)
    body_content = cache.get(cache_key)
    if body_content is None:
        html = github_report.get_html()
        # We want to handle complete HTML documents and also fragments. We're going to extract the contents of the body
        # at the end of this function, but it's easiest to normalize to complete documents because that's what the
        # HTML-wrangling libraries we're using are most comfortable handling.
        if "<html>" not in html:
            html = f"<html><body>{html}</body></head>"

        cleaned = Cleaner(
            page_structure=False, style=True, kill_tags=["head"]
        ).clean_html(html)

        soup = BeautifulSoup(cleaned, "html.parser")

        # For small screens we want to allow side-scrolling for just a small number of elements. To enable this each one
        # needs to be wrapped in a div that we can target for styling.
        for tag in ["table", "pre"]:
            for element in soup.find_all(tag):
                element.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

        body_content = "".join([str(element) for element in soup.body.contents])
        cache.set(cache_key, body_content, timeout=84600)
    return mark_safe(body_content)
