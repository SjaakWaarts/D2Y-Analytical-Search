"""
Definition of views.
"""

from datetime import datetime
import sys
import os
import subprocess
import shutil
import zipfile
import json
import urllib
import requests
import boto3
import io
import hashlib
from PIL import Image
from slugify import slugify
import logging
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse, FileResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail
from users_app.models import User
import seeker.esm as esm
import FMI.settings
from FMI.settings import BASE_DIR, ES_HOSTS, MEDIA_BUCKET, MEDIA_URL
from FMI.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import dhk_app.recipe_scrape as recipe_scrape
import app.aws as aws
import app.workbook as workbook
import app.wb_excel as wb_excel

logger = logging.getLogger(__name__)

class Recipe():
    id = None
    new = False
    recipe = {}
    reviews = []

    def __init__(self, id, recipe=None):
        self.id = id
        if recipe:
            self.recipe = recipe
            self.new = True;
        else:
            self.get(id)

    def get(self, id):
        self.recipe = self.es_get(id)
        self.carousel_get()

    def put(self):
        result = self.es_put()
        return result

    def carousel_get(self):
        folder_name = 'reviews/{}/'.format(slugify(self.recipe['id']))
        update = False
        images_s3 = aws.s3_list_images(MEDIA_BUCKET, folder_name)
        for image_s3 in images_s3:
            location = "{}{}".format(MEDIA_URL, image_s3['location'])
            try:
                slide_nr = int(image_s3['tags']['slide_nr'])
            except:
                slide_nr = -1
            found = False
            image_nr = 0
            for image in self.recipe['images']:
                if location == image['location']:
                    found = True
                    break
                image_nr = image_nr + 1
            if not found:
                update = True
                self.recipe['images'].append({
                    'type'     : 'media',
                    'location' : location
                    })
            image_s3['slide_nr'] = slide_nr if slide_nr > -1 else image_nr
            image_s3['image_nr'] = image_nr
        images_s3.sort(key=lambda x :x['slide_nr'])
        # Put slide in the right sequence
        for image_s3 in images_s3:
            if image_s3['slide_nr'] != image_s3['image_nr']:
                update = True
                slide = self.recipe['images'].pop(image_s3['image_nr'])
                self.recipe['images'].insert(image_s3['slide_nr'], slide)

        # Save in ES in case images/reviews have been added since last word reload
        if update:
            self.put()

    def carousel_put(self, carousel):
        folder_name = 'reviews/{}/'.format(slugify(self.recipe['id']))
        images = []
        # type: image - from upload, media - from reviews, search - from web search. First image is featured image
        for slide in carousel:
            if slide['type'] in ['image']:
                images.append({'type': slide['type'], 'location' : slide['location']})
            elif slide['type'] == 'media':
                key = slide['location'][len(MEDIA_URL):]
                if not slide['checked']:
                    aws.s3_delete(MEDIA_BUCKET, key)
                else:
                    tags = {'slide_nr' : str(len(images))}
                    aws.s3_update_tags(MEDIA_BUCKET, key, tags)
                    images.append({'type': slide['type'], 'location' : slide['location']})
            elif slide['type'] == 'search':
                if slide['checked']:
                    tags = {'slide_nr' : str(len(images))}
                    key = aws.s3_put_image(MEDIA_BUCKET, folder_name, None, slide['src'], tags=tags)
                    images.append({'type' : 'media', 'location' : "{}{}".format(MEDIA_URL, key)})
        self.recipe['images'] = images
        result = self.put()

    def cats_set(self, categories):
        self.recipe['categories'] = categories

    def tags_set(self, tags):
        self.recipe['tags'] = tags

    def clubs_set(self, clubs):
        if len(clubs) > 0:
            clubs.sort(key=lambda club: club['cooking_date'])
        for club in clubs:
            cook_user = User.objects.get(username=club['cook'])
            if 'position'not in club and len(club['address']) > 2:
                try:
                    geolocator = Nominatim(user_agent="dhk")
                    club['position'] = geolocator.geocode(club['address'])
                except (AttributeError, GeopyError):
                    pass
        self.recipe['cooking_clubs'] = clubs
    
    def es_get(self, id):
        es_host = ES_HOSTS[0]
        results = esm.get_doc(es_host, 'recipes', id)
        results = json.loads(results.text)
        recipe = results.get('_source', None)
        return recipe

    def es_put(self):
        es_host = ES_HOSTS[0]
        s, search_q = esm.setup_search()
        result = esm.put_doc(es_host, 'recipes', self.id, self.recipe)
        return result

    def es_filter_one(self, field_name, field_value):
        es_host = ES_HOSTS[0]
        s, search_q = esm.setup_search()
        search_filters = search_q["query"]["bool"]["filter"]
        field = field_name + '.keyword'
        terms = [field_value]
        terms_filter = {"terms": {field: terms}}
        search_filters.append(terms_filter)
        search_aggs = search_q["aggs"]

        results = esm.search_query(es_host, 'recipes', search_q)
        results = json.loads(results.text)
        hits = results.get('hits', {})
        hit = hits.get('hits', [{}])[0]
        recipe = hit.get('_source', {})
        return recipe

    def screen_title(self):
        recipe_title = self.recipe['title']
        try:
            recipe_title = recipe_title[0].upper() + recipe_title[1:].lower()
        except:
            recipe_title = ""
        self.recipe['title'] = recipe_title
        for course in self.recipe['courses']:
            course_title = course['title']
            try:
                course_title = course_title[0].upper() + course_title[1:].lower()
            except:
                course_title = recipe_title
            course['title'] = course_title

    def screen_categories(self):
        categories = self.recipe['categories']
        categories_new = []
        for categorie in categories:
            try:
                categorie = categorie[0].upper() + categorie[1:].lower()
            except:
                categorie = ""
            if categorie and categorie not in categories_new:
                for cat, subs in recipe_scrape.taxonomy.items():
                    if categorie == cat or categorie in subs:
                        categories_new.append(categorie)
                        break
        self.recipe['categories'] = categories_new

    def screen(self):
        # Screening rules
        # Title: Start with capital, rest lowercase
        # Categories: Start with capital, rest lowercase
        self.screen_title()
        self.screen_categories()


def recipe_view(request):
    """Renders dhk page."""
    id = request.GET['id']
    recipe = Recipe(id)
    context = {
        'site' : FMI.settings.site,
        'year':datetime.now().year,
        'recipe'  : recipe.recipe,
        }
    return render(
        request,
        'dhk_app/recipe.html',
        context,
        content_type='text/html'
    )

def recipe_edit_view(request):
    """Renders dhk page."""
    id = request.GET['id']
    recipe_obj = Recipe(id)
    dhk_wb = workbook.Workbook('dhk')
    facets = {
        'categories' : {'keyword' : True, 'nested' : None, 'options' : {'size' : 100, 'order' : {'_key' : 'asc' }}},
        'tags' : {'keyword' : True, 'nested' : None, 'options' : {'size' : 100, 'order' : {'_key' : 'asc' }}},
        }
    aggs = dhk_wb.aggs(facets)
    cats_buckets = aggs['categories']['buckets']
    tags_buckets = aggs['tags']['buckets']
    context = {
        'site' : FMI.settings.site,
        'year':datetime.now().year,
        'recipe'  : recipe_obj.recipe,
        'cats_buckets' : cats_buckets,
        'tags_buckets' : tags_buckets,
        }
    return render(
        request,
        'dhk_app/recipe_edit.html',
        context,
        content_type='text/html'
    )

def recipe_carousel_images_search(request):
    id = request.GET['id']
    q = request.GET['q']
    thumbnails = recipe_scrape.carousel_scrape(q, 20)
    #for image_url in image_urls:
    #    persist_image('images', image_url)
    context = {
        'thumbnails' : thumbnails
        }
    return HttpResponse(json.dumps(context), content_type='application/json')

# prevent CsrfViewMiddleware from reading the POST stream
#@csrf_exempt
@requires_csrf_token
def recipe_carousel_post(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    id = json_data.get('id', None)
    carousel = json_data.get('carousel', None)
    recipe_obj = Recipe(id)
    recipe_obj.carousel_put(carousel)
    context = {
        'recipe' : recipe_obj.recipe,
        'reviews' : recipe_obj.reviews
        }
    return HttpResponse(json.dumps(context), content_type='application/json')

def recipe_get(request):
    id = request.GET['id']
    format = request.GET['format']
    logger.info(f"Obtain recipe for id '{id}'")
    recipe_obj = Recipe(id)
    context = {
        'recipe'  : recipe_obj.recipe,
        'reviews' : recipe_obj.reviews
        }
    if format == 'json':
        return HttpResponse(json.dumps(context), content_type='application/json')
    else:
        recipe_basename = id
        dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'recipes')
        zip_filename = recipe_basename + '.zip'
        zip_fullname = os.path.join(dirname, zip_filename)
        zip_dirname = os.path.join(dirname, recipe_basename)
        shutil.make_archive(zip_dirname, 'zip', zip_dirname)
        recipe_fullname = os.path.join(dirname, recipe_basename + '.docx')
        pfd_fullname = os.path.join(dirname, recipe_basename + '.pdf')
        shutil.copy(zip_fullname, recipe_fullname)
        if sys.platform[0:3] == "win":
            f = open(recipe_fullname, 'rb')
            filename = recipe_basename + '.docx'
        else:
            cmd = ['soffice', '--headless', '--convert-to', 'pdf','--outdir', dirname, recipe_fullname]
            #process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).wait()
            f = open(pfd_fullname, 'rb')
            filename = recipe_basename + '.pdf'
            os.remove(recipe_fullname)
        os.remove(zip_fullname)
        #response = Response(pdf.read(), content_type='application/pdf')
        #response.content_disposition = 'inline;filename=' + basename
        return FileResponse(f, as_attachment=True, filename=filename)


# prevent CsrfViewMiddleware from reading the POST stream
#@csrf_exempt
@requires_csrf_token
def recipe_post(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    recipe_new = json_data.get('recipe', None)
    recipe_obj = Recipe(recipe_new['id'])
    recipe_obj.clubs_set(recipe_new['cooking_clubs'])
    recipe_obj.cats_set(recipe_new['categories'])
    recipe_obj.tags_set(recipe_new['tags'])
    result = recipe_obj.put()

    sender = "info@deheerlijkekeuken.nl"
    for club in recipe_obj.recipe['cooking_clubs']:
        cooking_date = datetime.strptime(club['cooking_date'], "%Y-%m-%dT%H:%M")
        subject = "Kookclub {0} bij {1}".format(cooking_date.strftime('%m %b %Y - %H:%M'), club['cook'])
        message = \
            """Uitnodiging kookclub\n\n
            {0}\n\n
            Kosten per persoon: € {1}]n\n
            {2}\n\n
            Adres\n
            {3}\n
            {4}\n
            {5}\n\n
            Gasten:\n""".format(
            recipe.recipe['title'], club['cost'], club['invitation'],
            cook_user.first_name + " " + cook_user.last_name,
            cook_user.street + " " + cook_user.housenumber,
            cook_user.zip + " " + cook_user.city)
        to_list = [club['email']]
        for participant in club['participants']:
            to_list.append(participant['email'])
            message = message + "{0}\t{1}\n".format(participant['user'], participant['comment'])
        html_message = loader.render_to_string('dhk_app/club_mail.html',
                                               {'recipe': recipe_obj.recipe, 'club': club})
        send_mail(subject, message, sender, to_list, html_message=html_message, fail_silently=True)
    context = {
        'recipe' : recipe_obj.recipe,
        'reviews' : recipe_obj.reviews
        }
    return HttpResponse(json.dumps(context), content_type='application/json')

