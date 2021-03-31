from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from social_django.utils import load_backend, load_strategy
from social_django.views import complete


def landing(request):
    return render(request, "landing.html")


@never_cache
@csrf_exempt
def nhsid_complete(request, *args, **kwargs):
    """
    Return the complete view with expected arguments. A successful authentication from NHS ID returns to
    /auth. social_django expects to find the backend name in the url (by default /complete/<backend>)
    """
    backend = "nhsid"
    uri = reverse("gateway:nhsid_complete")
    request.social_strategy = load_strategy(request)
    request.backend = load_backend(request.social_strategy, backend, uri)
    return complete(request, backend, *args, **kwargs)
