from model_bakery.recipe import Recipe

from .models import Category, Output


category, _ = Category.objects.get_or_create(name="Reports")

real_output = Recipe(
    Output,
    category=category,
    menu_name="test",
    repo="output-explorer-test-repo",
    branch="master",
    output_html_file_path="test-outputs/output.html",
)

dummy_output = Recipe(
    Output,
    category=category,
    menu_name="test",
    repo="test-repo",
    output_html_file_path="output.html",
)
