from model_bakery.recipe import Recipe

from .models import Category, Report


category, _ = Category.objects.get_or_create(name="Reports")

real_report = Recipe(
    Report,
    category=category,
    menu_name="test",
    repo="output-explorer-test-repo",
    branch="master",
    output_html_file_path="test-outputs/output.html",
)

dummy_report = Recipe(
    Report,
    category=category,
    menu_name="test",
    repo="test-repo",
    output_html_file_path="report.html",
)
