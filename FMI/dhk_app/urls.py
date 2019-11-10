from django.urls import path
import app.models as models
from dhk_app import views
from dhk_app import dhk_admin
from dhk_app import club
from dhk_app import kitchen
from dhk_app import workshops
from dhk_app import recipe


urlpatterns = [
    path('', views.dhk_view, name='dhk'),
    path('dhk_admin', dhk_admin.dhk_admin_view, name='dhk/dhk_admin'),
    path('delete_recipe', dhk_admin.delete_recipe, name='dhk/delete_recipe'),
    path('upload_file', dhk_admin.upload_file, name='dhk/upload_file'),
    path('get_uploaded_files', dhk_admin.get_uploaded_files, name='dhk/get_uploaded_files'),
    path('club', club.club_view, name='dhk/club'),
    path('get_cooking_clubs', club.get_cooking_clubs, name='dhk/get_cooking_clubs'),
    path('kitchen', kitchen.kitchen_view, name='dhk/kitchen'),
    path('workshops', workshops.workshops_view, name='dhk/workshops'),
    path('recipe', recipe.recipe_view, name='dhk/recipe'),
    path('get_recipe', recipe.get_recipe, name='dhk/get_recipe'),
    path('post_recipe', recipe.post_recipe, name='dhk/post_recipe'),
    path('search', models.ExcelSeekerView.as_view(), name='dhk/search'),
]