from django import template

from ..rendering import process_html


register = template.Library()


@register.simple_tag(takes_context=True)
def category_reports_for_user(context, category):
    """Filter out draft reports in a category if the current user is not logged in, or doesn't have permission"""
    user = context["user"]
    return category.reports.for_user(user)


@register.simple_tag
def render_html(remote_cls):
    """
    Render HTML from a "remote" class instance

    We cache the rendered report template so we don't want to pull the HTML via
    the given remote class on each page load.  This allows us to call the
    process_html function inside the cached template fragment named `report_content`.
    """
    return process_html(remote_cls.get_html())
