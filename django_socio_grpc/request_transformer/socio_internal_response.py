from django.http import HttpResponse


class InternalHttpResponse(HttpResponse):
    """
    Class mocking django.http.HttpResponse to make some django behavior like middleware and cache still work.
    """

    def __init__(self, grpc_context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = dict(grpc_context.trailing_metadata())
