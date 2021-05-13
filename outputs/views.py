import structlog
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
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
    extracted = github_output.get_html()
    return TemplateResponse(
        request,
        "outputs/output.html",
        {
            "notebook_contents": extracted["body"],
            "output": github_output.output,
        },
    )
