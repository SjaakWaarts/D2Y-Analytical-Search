"""
Definition of views.
"""

from datetime import datetime
import re
import sys
import os
import subprocess
import shutil
import zipfile
import docx
import json
import urllib
import requests
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse, FileResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail
from users_app.models import User
import seeker.esm as esm
import FMI.settings
from FMI.settings import BASE_DIR, ES_HOSTS


def recipe_view(request):
    """Renders dhk page."""
    id = request.GET['id']
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    search_filters = search_q["query"]["bool"]["filter"]
    field = 'id.keyword'
    terms = [id]
    terms_filter = {"terms": {field: terms}}
    search_filters.append(terms_filter)
    search_aggs = search_q["aggs"]

    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    hit = hits.get('hits', [{}])[0]
    recipe = hit.get('_source', {})
    context = {
        'site' : FMI.settings.site,
        'year':datetime.now().year,
        'recipe'  : recipe,
        }
    return render(
        request,
        'dhk_app/recipe.html',
        context
    )

def get_recipe(request):
    id = request.GET['id']
    format = request.GET['format']
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    search_filters = search_q["query"]["bool"]["filter"]
    field = 'id.keyword'
    terms = [id]
    terms_filter = {"terms": {field: terms}}
    search_filters.append(terms_filter)
    search_aggs = search_q["aggs"]

    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    hit = hits.get('hits', [{}])[0]
    recipe = hit.get('_source', {})
    context = {
        'recipe'  : recipe,
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
def post_recipe(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    recipe = json_data.get('recipe', None)
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    if len(recipe['cooking_clubs']) > 0:
        recipe['cooking_clubs'].sort(key=lambda cooking_club: cooking_club['cooking_date'])
    for cooking_club in recipe['cooking_clubs']:
        cook_user = User.objects.get(username=cooking_club['cook'])
        if 'position'not in cooking_club and len(cooking_club['address']) > 2:
            try:
                geolocator = Nominatim(user_agent="dhk")
                cooking_club['position'] = geolocator.geocode(cooking_club['address'])
            except (AttributeError, GeopyError):
                pass
    result = esm.update_doc(es_host, 'recipes', recipe['id'], recipe)

    sender = "info@deheerlijkekeuken.nl"
    for cooking_club in recipe['cooking_clubs']:
        cooking_date = datetime.strptime(cooking_club['cooking_date'], "%Y-%m-%dT%H:%M")
        subject = "Kookclub {0} bij {1}".format(cooking_date.strftime('%m %b %Y - %H:%M'), cooking_club['cook'])
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
            recipe['title'], cooking_club['cost'], cooking_club['invitation'],
            cook_user.first_name + " " + cook_user.last_name,
            cook_user.street + " " + cook_user.housenumber,
            cook_user.zip + " " + cook_user.city)
        to_list = [cooking_club['email']]
        for participant in cooking_club['participants']:
            to_list.append(participant['email'])
            message = message + "{0}\t{1}\n".format(participant['user'], participant['comment'])
        send_mail(subject, message, sender, to_list, fail_silently=True)
    context = {
        'recipe' : recipe
        }
    return HttpResponse(json.dumps(context), content_type='application/json')


