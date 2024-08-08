from django.http import HttpResponse


class InternalHttpResponse(HttpResponse):
    """
    Class mocking django.http.HttpResponse to make some django behavior like middleware and cache still work.
    """
