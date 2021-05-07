from .models import Output


def outputs(request):
    return {
        "outputs": [
            {"menu_name": output.menu_name, "slug": output.slug}
            for output in Output.objects.all()
        ]
    }
