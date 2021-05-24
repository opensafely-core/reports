from datetime import date, timedelta
from uuid import uuid4

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from model_bakery import baker

from outputs.models import Category, Output
from outputs.views import process_html


@pytest.mark.django_db
def test_landing_view(client):
    """Test landing view context"""
    assert Output.objects.exists() is False
    # By default we have one Category, set up in the migration
    assert Category.objects.count() == 1
    response = client.get(reverse("gateway:landing"))

    # There is a category, but it isn't included in the context because it has no associated Outputs
    assert list(response.context["categories"]) == []

    # when Outputs exist, their categories are included in the context
    baker.make_recipe("outputs.dummy_output")
    baker.make_recipe("outputs.dummy_output", menu_name="test1")
    response = client.get(reverse("gateway:landing"))
    assert list(response.context["categories"]) == list(Category.objects.all())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "outputs,expected",
    [
        (
            {
                "test1": {"publication_date": date(2021, 2, 1)},
                "test2": {
                    "publication_date": date(2021, 1, 1),
                    "last_updated": date(2021, 3, 1),
                },
            },
            [
                ("test2", "updated", date(2021, 3, 1)),
                ("test1", "published", date(2021, 2, 1)),
                ("test2", "published", date(2021, 1, 1)),
            ],
        ),
        (
            {
                "test1": {"publication_date": date(2021, 2, 1)},
                "test2": {
                    "publication_date": date(2021, 1, 1),
                    "last_updated": date(2021, 1, 1),
                },
            },
            [
                ("test1", "published", date(2021, 2, 1)),
                ("test2", "published", date(2021, 1, 1)),
            ],
        ),
        (
            # setup 12 outputs published on 1st, 2nd, ...12th
            {
                f"test{i}": {"publication_date": date(2021, 1, 1) + timedelta(days=i)}
                for i in range(12)
            },
            # expect 11 outputs published on 10th, 9th, ...1st
            [
                (
                    f"test{11 - i}",
                    "published",
                    date(2021, 1, 1) + timedelta(days=(11 - i)),
                )
                for i in range(10)
            ],
        ),
    ],
    ids=[
        "Test outputs with both publication and last updated are included, in reverse order",
        "Test outputs with identical publication and updated dates only show publication",
        "Test only 10 most recent events are shown",
    ],
)
def test_landing_view_recent_activity(client, outputs, expected):
    for menu_name, output_fields in outputs.items():
        baker.make_recipe("outputs.dummy_output", menu_name=menu_name, **output_fields)

    response = client.get(reverse("gateway:landing"))
    # only outputs with dates are shown in recent_activity
    # output activity is returned in reverse date order
    # outputs have additional annotation fields "activity" and "activity_date"
    context_output = [
        (output.menu_name, output.activity, output.activity_date)
        for output in response.context["recent_activity"]
    ]
    assert context_output == expected


@pytest.mark.django_db
def test_output_view(client):
    """Test a single output page"""
    # output for a real file
    output = baker.make_recipe("outputs.real_output")
    response = client.get(output.get_absolute_url())
    assert_html_equal(
        response.context["notebook_contents"],
        """
            <h1>A Test Output HTML file</h1>
            <p>The test content</p>
        """,
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
    assert response.url == output.get_absolute_url()


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
    output = baker.make_recipe("outputs.real_output")

    # nothing cached yet
    response = client.get(output.get_absolute_url())
    assert_last_cache_log(
        log_output, {"output_id": output.id, "slug": "test", "event": "Cache missed"}
    )
    assert response.status_code == 200

    # fetch it again
    client.get(output.get_absolute_url())
    assert_last_cache_log(log_output, None)
    assert response.status_code == 200

    # force update
    response = client.get(output.get_absolute_url() + "?force-update=")
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
    assert response.url == output.get_absolute_url()


@pytest.mark.parametrize(
    "html",
    [
        b"""
            <!DOCTYPE html>
            <html>
                <head>
                    <style type="text/css">body {margin: 0;}</style>
                    <style type="text/css">a {background-color: red;}</style>
                    <script src="https://a-js-package.js"></script>
                </head>
                <body>
                    <p>foo</p>
                    <div>Stuff</div>
                </body>
            </html>
        """,
        b"""
            <html>
                <body>
                    <p>foo</p>
                    <div>Stuff</div>
                </body>
            </html>
        """,
        b"""
            <p>foo</p>
            <div>Stuff</div>
        """,
        b"""
            <script>Some Javascript nonsense</script>
            <p>foo</p>
            <div>
                Stuff
                <script>Some more Javascript nonsense</script>
            </div>
        """,
        b"""
            <style>Mmmm, lovely styles...</style>
            <p>foo</p>
            <div>
                Stuff
                <style>MOAR STYLZ</style>
            </div>
        """,
    ],
    ids=[
        "Extracts body from HTML full document",
        "Extracts body from HTML document without head",
        "Returns HTML without body tags unchanged",
        "Strips out all script tags",
        "Strips out all style tags",
    ],
)
def test_html_processing(html):
    assert_html_equal(
        process_html(html),
        """
            <p>foo</p>
            <div>Stuff</div>
        """,
    )


def assert_html_equal(actual, expected):
    assert normalize(actual) == normalize(expected)


def normalize(html):
    return BeautifulSoup(html.strip(), "html.parser").prettify()
