from bs4 import BeautifulSoup


def assert_html_equal(actual, expected):
    assert normalize(actual) == normalize(expected)


def normalize(html):
    return BeautifulSoup(html.strip(), "html.parser").prettify()
