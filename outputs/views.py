import structlog
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control

from .github import GithubReport
from .models import Report


logger = structlog.getLogger()


@cache_control(cache_timeout=86400)
def report_view(request, slug, cache_token):
    """
    Fetches an html report file from github, and renders the style and body tags within
    the report template page.  Caches for 24 hours, can be forced to refetch and update
    the cache with the `force-update` query parameter.
    """
    report = get_object_or_404(Report, slug=slug)
    if "force-update" in request.GET:
        # Force an update by refreshing the cache_token and redirecting
        report.refresh_cache_token()
        logger.info(
            "Cache token refreshed, redirecting...",
            report_id=report.pk,
            slug=report.slug,
        )
        return redirect(report.get_absolute_url())
    elif report.cache_token != cache_token:
        # If an invalid cache_token is encountered, redirect to the latest one
        logger.warn(
            "Cache token not found, redirecting...",
            report_id=report.pk,
            slug=report.slug,
        )
        return redirect(report.get_absolute_url())

    logger.info("Cache missed", report_id=report.pk, slug=report.slug)
    github_report = GithubReport(report)
    response = report_fetch_view(request, github_report)
    return response


def report_fetch_view(request, github_report):
    # Fetch the uncached report view
    return TemplateResponse(
        request,
        "outputs/report.html",
        {
            "notebook_contents": process_html(github_report.get_html()),
            "report": github_report.report,
        },
    )


def process_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Reports may be formatted as proper HTML documents, or just as fragments of HTML. In the former case we want
    # just the body, in the latter we want the whole thing.
    if soup.html:
        if soup.html.body:
            content = _contents_of_tag(soup.html.body)
        else:
            raise ValueError("HTML document has an <html>, but no <body>.")
    else:
        content = soup

    # As well as removing any <head>, we defensively remove <script> or <style> elements that may have been inserted
    # elsewhere in the document.
    for tag in ["script", "style"]:
        for element in content.find_all(tag):
            element.decompose()

    # For small screens we want to allow side-scrolling for just a small number of elements. To enable this each one needs to be
    # wrapped in a div that we can target for styling.
    for tag in ["table", "pre"]:
        for element in content.find_all(tag):
            element.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

    return mark_safe(str(content))


def _contents_of_tag(tag):
    # There isn't any way through the BeautifulSoup API to address the entire contents of a tag as a single
    # document-without-a-single-root-node. But the internals of the library can cope with such documents -- as long
    # as they are handed to the BeautifulSoup constructor. So we rip out the contents of this tag as a list of
    # strings and re-parse it.
    return BeautifulSoup(
        "".join([str(element) for element in tag.contents]), "html.parser"
    )
