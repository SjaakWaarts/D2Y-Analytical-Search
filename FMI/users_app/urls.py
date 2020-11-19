from django.urls import path
from users_app import views
from users_app.models import LogMessage

home_list_view = views.HomeListView.as_view(
    queryset=LogMessage.objects.order_by("-log_date")[:5],  # :5 limits the results to the five most recent
    context_object_name="message_list",
    template_name="users_app/users_app.html",
)

urlpatterns = [
    path("log/", views.log_message, name="log"),
    path("register/", views.register, name='users_app/register'),
    path("login/", views.login, name='users_app/login'),
    path("logout/", views.logout, name='users_app/logout'),
    path("unlock/", views.unlock, name='users_app/unlock'),
    #path('accounts/register/', views.register, name='register'),
    path('register_complete/', views.registrer_complete, name='users_app/register_complete'),
    path("profile/", views.profile, name='users_app/profile'),
    # SAML
    path('saml/index', views.saml_index, name='users_app/saml/index'),
    path('saml/attrs', views.saml_attrs, name='users_app/saml/attrs'),
    path('saml/metadata', views.saml_metadata, name='users_app/saml/metadata')
]