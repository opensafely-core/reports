from os import environ

from .models import Output


def show_login(request):
    return {"show_login": environ.get("SHOW_LOGIN", False)}


def outputs(request):
    return {
        "outputs": [
            {"menu_name": output.menu_name, "slug": output.slug}
            for output in Output.objects.all()
        ]
    }
