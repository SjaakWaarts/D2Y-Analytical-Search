from django.urls import path
from users_app.api.views import ObtainAuthToken, RefreshTokenView

urlpatterns = [
    path("", ObtainAuthToken.as_view(), name='authorize'),
    path("refresh/", RefreshTokenView.as_view(), name='refresh'),
]