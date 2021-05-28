from .models import Category


def reports(request):
    return {
        "categories": Category.populated.for_user(request.user),
    }
