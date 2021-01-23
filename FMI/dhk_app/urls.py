from django.urls import path
import app.models as models
from dhk_app import views
from dhk_app import dhk_admin
from dhk_app import club
from dhk_app import kitchen
from dhk_app import recipe
from dhk_app import workshops

app_name='dhk'
urlpatterns = [
    path('', views.dhk_view, name='home'),
    path('dhk_admin', dhk_admin.dhk_admin_view, name='dhk_admin'),
    path('delete_recipe', dhk_admin.delete_recipe, name='delete_recipe'),
    path('upload_file', dhk_admin.upload_file, name='upload_file'),
    path('get_uploaded_files', dhk_admin.get_uploaded_files, name='get_uploaded_files'),
    path('club', club.club_view, name='club'),
    path('get_cooking_clubs', club.get_cooking_clubs, name='get_cooking_clubs'),
    path('kitchen', kitchen.kitchen_view, name='kitchen'),
    path('workshops', workshops.workshops_view, name='workshops'),
    path('get_workshops', workshops.get_workshops, name='get_workshops'),
    path('recipe', recipe.recipe_view, name='recipe'),
    path('recipe_edit', recipe.recipe_edit_view, name='recipe_edit'),
    path('recipe_get', recipe.recipe_get, name='recipe_get'),
    path('recipe_post', recipe.recipe_post, name='recipe_post'),
    path('recipe_carousel_images_search', recipe.recipe_carousel_images_search, name='recipe_carousel_images_search'),
    path('recipe_carousel_post', recipe.recipe_carousel_post, name='recipe_carousel_post'),
    path('search', models.ExcelSeekerView.as_view(), name='search'),
]