import structlog
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control

from .github import GitHubOutput
from .models import Output


logger = structlog.getLogger()


@cache_control(cache_timeout=86400)
def output_view(request, slug, cache_token):
    """
    Fetches an html output file from github, and renders the style and body tags within
    the output template page.  Caches for 24 hours, can be forced to refetch and update
    the cache with the `force-update` query parameter.
    """
    output = get_object_or_404(Output, slug=slug)
    if "force-update" in request.GET:
        # Force an update by refreshing the cache_token and redirecting
        output.refresh_cache_token()
        logger.info(
            "Cache token refreshed, redirecting...",
            output_id=output.pk,
            slug=output.slug,
        )
        return redirect(output.get_absolute_url())
    elif output.cache_token != cache_token:
        # If an invalid cache_token is encountered, redirect to the latest one
        logger.warn(
            "Cache token not found, redirecting...",
            output_id=output.pk,
            slug=output.slug,
        )
        return redirect(output.get_absolute_url())

    logger.info("Cache missed", output_id=output.pk, slug=output.slug)
    github_output = GitHubOutput(output)
    response = output_fetch_view(request, github_output)
    return response


def output_fetch_view(request, github_output):
    # Fetch the uncached output view
    return TemplateResponse(
        request,
        "outputs/output.html",
        {
            "notebook_contents": process_html(github_output.get_html()),
            "output": github_output.output,
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
    for table in content.find_all("table"):
        table.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

    return mark_safe(str(content))


def _contents_of_tag(tag):
    # There isn't any way through the BeautifulSoup API to address the entire contents of a tag as a single
    # document-without-a-single-root-node. But the internals of the library can cope with such documents -- as long
    # as they are handed to the BeautifulSoup constructor. So we rip out the contents of this tag as a list of
    # strings and re-parse it.
    return BeautifulSoup(
        "".join([str(element) for element in tag.contents]), "html.parser"
    )
