import structlog
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .github import GitHubOutput
from .models import Output


logger = structlog.getLogger()


def output_view(request, slug):
    """
    Fetches an html output file from github, and renders the style and body tags within
    the output template page.  Caches for 24 hours, can be forced to refetch and update
    the cache with the `force-update` query parameter.
    """
    output = get_object_or_404(Output, slug=slug)
    cache_key = output.slug
    response = cache.get(cache_key)
    if response is None or "force-update" in request.GET:
        # not cached or force-update requested; fetch it and cache for 24 hrs
        if "force-update" in request.GET:
            logger.info("Cache update forced", key=cache_key)
        else:
            logger.info("Cache missed", key=cache_key)
        github_output = GitHubOutput(output)
        response = output_fetch_view(request, github_output)
        if response.status_code == 200:
            response.add_post_render_callback(
                lambda resp: cache.set(cache_key, resp, timeout=86400)
            )
    else:
        logger.info("Cache hit", key=cache_key)

    return response


def output_fetch_view(request, github_output):
    # Fetch the uncached output view
    extracted = github_output.get_html()
    return TemplateResponse(
        request,
        "outputs/output.html",
        {
            "notebook_style": extracted["style"],
            "notebook_contents": extracted["body"],
            "output": github_output.output,
        },
    )
