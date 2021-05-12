from .models import Output


def outputs(request):
    return {"outputs": Output.objects.all()}
