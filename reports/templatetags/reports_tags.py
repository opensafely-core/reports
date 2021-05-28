from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def category_reports_for_user(context, category):
    """Filter out draft reports in a category if the current user is not logged in, or doesn't have permission"""
    user = context["user"]
    return category.reports.for_user(user)
