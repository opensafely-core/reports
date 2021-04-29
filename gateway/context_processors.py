from os import environ


def show_login(request):
    return {"show_login": environ.get("SHOW_LOGIN", False)}
