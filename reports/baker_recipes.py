from model_bakery.recipe import Recipe

from .models import Category, Org, Report


category, _ = Category.objects.get_or_create(name="Reports")
bennett, _ = Org.objects.get_or_create(slug="bennett")

real_report = Recipe(
    Report,
    category=category,
    org=bennett,
    title="test",
    repo="output-explorer-test-repo",
    branch="master",
    report_html_file_path="test-outputs/output.html",
)

dummy_report = Recipe(
    Report,
    category=category,
    org=bennett,
    title="test",
    repo="test-repo",
    report_html_file_path="report.html",
)
