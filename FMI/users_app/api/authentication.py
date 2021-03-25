from functools import wraps

from django.http import HttpResponseForbidden
from django.utils.decorators import available_attrs

from api.v1.models import Token
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication, SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class TokenAuthentication(BaseTokenAuthentication):
    """
    Extends default token auth to support time-based expiration
    """

    model = Token

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed("Ongeldige token")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("Gebruiker inactief of bestaat niet")

        if token.expired():
            raise exceptions.AuthenticationFailed("Token is verlopen")

        return token.user, token


def token_or_cookie_required(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        try:
            if TokenAuthentication().authenticate(request):
                return view_func(request, *args, **kwargs)
            elif request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            else:
                raise exceptions.AuthenticationFailed
        except exceptions.AuthenticationFailed:
            return HttpResponseForbidden()
    return _wrapped_view

