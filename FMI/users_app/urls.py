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
    path("register/", views.register, name='register'),
    #path('accounts/register/', views.register, name='register'),
    path('register_complete/', views.registrer_complete, name='register_complete'),
    path("profile/", views.profile, name='profile')
]