from datetime import datetime, timedelta

import pytest
from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from outputs.models import Output


@pytest.mark.django_db
def test_landing_view(client):
    """Test landing view context"""
    assert Output.objects.exists() is False
    response = client.get(reverse("gateway:landing"))
    assert response.context["outputs"] == []

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
    assert response.context["outputs"] == [
        {"menu_name": "test", "slug": "test"},
        {"menu_name": "test1", "slug": "test1"},
    ]


@pytest.mark.django_db
def test_output_view(client):
    """Test a single output page"""
    # output for a real file
    output = baker.make_recipe("outputs.real_output")
    response = client.get(reverse("outputs:output_view", args=(output.slug,)))
    assert response.context["notebook_style"] == [
        '<style type="text/css">body {margin: 0;}</style>',
        '<style type="text/css">a {background-color: blue;}</style>',
    ]
    assert (
        response.context["notebook_contents"]
        == "\n<h1>A Test Output HTML file</h1>\n<p>The test content\t\n</p>"
    )


def assert_last_log(log_entries, expected_log_items):
    last_log = log_entries.entries[-1]
    for key, value in expected_log_items.items():
        assert last_log[key] == value


@pytest.mark.django_db
def test_output_view_cache(client, log_output):
    """
    Test caching a single output page.  Cache is updated if last updated date changed,
    """
    cache.clear()
    todays_date = datetime.today()
    last_updated = todays_date - timedelta(days=1)
    output = baker.make_recipe("outputs.real_output", last_updated=last_updated)

    # response is cached by slug
    # nothing cached yet
    assert cache.get("test") is None
    client.get(reverse("outputs:output_view", args=(output.slug,)))
    assert_last_log(log_output, {"key": "test", "event": "Cache missed"})
    assert cache.get("test") is not None

    # fetch it again
    client.get(reverse("outputs:output_view", args=(output.slug,)))
    assert_last_log(log_output, {"key": "test", "event": "Cache hit"})

    # force update
    client.get(reverse("outputs:output_view", args=(output.slug,)) + "?force-update=")
    assert_last_log(log_output, {"key": "test", "event": "Cache update forced"})

    # fetch it again
    client.get(reverse("outputs:output_view", args=(output.slug,)))
    assert_last_log(log_output, {"key": "test", "event": "Cache hit"})
