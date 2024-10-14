from rest_framework.filters import OrderingFilter as RestOrderingFilter


class OrderingFilter(RestOrderingFilter):
    def get_ordering(self, request, queryset, view):
        """
        Allow ordering with direct array value as grpc can pass array directly for ordering
        where REST Ordering is set by a comma delimited ?ordering=... query parameter.

        The `ordering` query parameter can be overridden by setting
        the `ordering_param` value on the OrderingFilter or by
        specifying an `ORDERING_PARAM` value in the API settings.

        Direct link of DRF OrderingFilter: https://github.com/encode/django-rest-framework/blob/master/rest_framework/filters.py
        """
        params = request.query_params.get(self.ordering_param)
        if params:
            if isinstance(params, str):
                params = params.split(",")
            fields = [param.strip() for param in params]
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)
