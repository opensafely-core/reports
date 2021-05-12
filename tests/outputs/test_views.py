from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from outputs.models import Output


@pytest.mark.django_db
def test_landing_view(client, settings):
    """Test landing view context"""
    settings.CACHE_MIDDLEWARE_SECONDS = 0
    assert Output.objects.exists() is False
    response = client.get(reverse("gateway:landing"))
    assert list(response.context["outputs"]) == []

    # when Outputs exist, they are included in the context
    baker.make(
        Output, menu_name="test", repo="test-repo", output_html_file_path="output.html"
    )
    baker.make(
        Output,
        menu_name="test1",
        repo="test-repo",
        output_html_file_path="output1.html",
    )
    response = client.get(reverse("gateway:landing"))
    assert list(response.context["outputs"]) == list(Output.objects.all())


@pytest.mark.django_db
def test_output_view(client):
    """Test a single output page"""
    # output for a real file
    output = baker.make_recipe("outputs.real_output")
    response = client.get(
        reverse("outputs:output_view", args=(output.slug, output.cache_token))
    )
    assert response.context["notebook_style"] == [
        '<style type="text/css">body {margin: 0;}</style>',
        '<style type="text/css">a {background-color: blue;}</style>',
    ]
    assert (
        response.context["notebook_contents"]
        == "\n<h1>A Test Output HTML file</h1>\n<p>The test content\t\n</p>"
    )


@pytest.mark.django_db
def test_output_view_with_invalid_token(client):
    """Test a single output page"""
    # output for a real file
    output = baker.make_recipe("outputs.real_output")
    invalid_uuid = uuid4()
    response = client.get(
        reverse("outputs:output_view", args=(output.slug, invalid_uuid))
    )
    assert response.status_code == 302
    assert response.url == reverse(
        "outputs:output_view", args=(output.slug, output.cache_token)
    )


def assert_last_cache_log(log_entries, expected_log_items):
    last_cache_log = next(
        (
            log
            for log in reversed(log_entries.entries)
            if "cache" in log["event"].lower()
        ),
        None,
    )
    if expected_log_items is None:
        assert last_cache_log is None
    else:
        for key, value in expected_log_items.items():
            assert last_cache_log[key] == value
    log_entries.entries.clear()


@pytest.mark.django_db
def test_output_view_cache(client, log_output):
    """
    Test caching a single output page.
    """
    cache.clear()
    todays_date = datetime.today()
    last_updated = todays_date - timedelta(days=1)
    output = baker.make_recipe("outputs.real_output", last_updated=last_updated)

    # nothing cached yet
    response = client.get(
        reverse("outputs:output_view", args=(output.slug, output.cache_token))
    )
    assert_last_cache_log(
        log_output, {"output_id": output.id, "slug": "test", "event": "Cache missed"}
    )
    assert response.status_code == 200

    # fetch it again
    client.get(reverse("outputs:output_view", args=(output.slug, output.cache_token)))
    assert_last_cache_log(log_output, None)
    assert response.status_code == 200

    # force update
    response = client.get(
        reverse("outputs:output_view", args=(output.slug, output.cache_token))
        + "?force-update="
    )
    old_token = output.cache_token
    output.refresh_from_db()
    assert old_token != output.cache_token
    assert_last_cache_log(
        log_output,
        {
            "output_id": output.id,
            "slug": "test",
            "event": "Cache token refreshed, redirecting...",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse(
        "outputs:output_view", args=(output.slug, output.cache_token)
    )
