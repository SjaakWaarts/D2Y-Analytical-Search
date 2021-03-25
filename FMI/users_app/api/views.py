from django.contrib.auth import user_logged_in
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users_app.api.authentication import TokenAuthentication
from users_app.api.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken as BaseObtainAuthToken
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class ObtainAuthToken(BaseObtainAuthToken):
    """
    View enabling username/password exchange for expiring token.
    """

    model = Token

    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.select_for_update().get_or_create(user=user)

            if token.expired():
                # If the token is expired, generate a new one.
                token.delete()
                token = Token.objects.create(user=user)

            user_logged_in.send(sender=user.__class__, request=request, user=user)

            data = {'token': token.key}
            return Response(data)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({'token-refreshed': True})
