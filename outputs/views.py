import structlog
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .github import get_html, get_repo
from .models import Output


logger = structlog.getLogger()


def output_view_cache_key(output, sha):
    return f"{output.slug}_{sha}"


def output_view(request, slug):
    """
    Fetches an html output file from github, and renders the style and body tags within
    the output template page.  Caches for 24 hours.
    """
    output = get_object_or_404(Output, slug=slug)
    # Get the repo and find the last commit sha.  Fetch cached response by repo and sha.
    repo = get_repo(output)
    last_commit_sha = repo.get_commits()[0].sha
    cache_key = output_view_cache_key(output, last_commit_sha)
    response = cache.get(cache_key)
    if response is None:
        # not cached; fetch it and cache for 24 hrs
        logger.info("Cache missed", key=cache_key)
        response = output_fetch_view(request, repo, output)
        if response.status_code == 200:
            response.add_post_render_callback(
                lambda resp: cache.set(cache_key, resp, timeout=86400)
            )
    else:
        logger.info("Cache hit", key=cache_key)

    return response


def output_fetch_view(request, repo, output):
    # Fetch the uncached output view
    extracted = get_html(repo, output)
    return TemplateResponse(
        request,
        "outputs/output.html",
        {"notebook_style": extracted["style"], "contents": extracted["body"]},
    )
