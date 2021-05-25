from .models import Category


def reports(request):
    return {
        "categories": Category.populated.all(),
    }
