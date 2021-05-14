from .models import Category


def outputs(request):
    return {"categories": Category.populated.all()}
