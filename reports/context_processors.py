from .models import Category


def reports(request):
    return {
        "categories": Category.populated.allowed_for_user(request.user),
    }
