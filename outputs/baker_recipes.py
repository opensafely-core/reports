from model_bakery.recipe import Recipe

from .models import Output


real_output = Recipe(
    Output,
    menu_name="test",
    repo="output-explorer-test-repo",
    branch="master",
    output_html_file_path="test-outputs/output.html",
)
