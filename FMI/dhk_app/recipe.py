"""
Definition of views.
"""

from datetime import datetime
import re
import sys
import os
import shutil
import json
import urllib
import requests
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail
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
    return HttpResponse(json.dumps(context), content_type='application/json')

# prevent CsrfViewMiddleware from reading the POST stream
#@csrf_exempt
@requires_csrf_token
def post_recipe(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    recipe = json_data.get('recipe', None)
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    result = esm.update_doc(es_host, 'recipes', recipe['id'], recipe)
    # Get the position from the address
    if len(recipe['cooking_clubs']) > 0:
        cooking_club = recipe['cooking_clubs'][-1]
        if 'position'not in cooking_club and len(cooking_club['address']) > 2:
            try:
                geolocator = Nominatim(user_agent="dhk")
                cooking_club['position'] = geolocator.geocode(cooking_club['address'])
            except (AttributeError, GeopyError):
                pass
        sender = "info@deheerlijkekeuken.nl"
        for cooking_club in recipe['cooking_clubs']:
            cooking_date = datetime.strptime(cooking_club['cooking_date'], "%Y-%m-%dT%H:%M")
            subject = "Kookclub {0} bij {1}".format(cooking_date.strftime('%m %b %Y - %H:%M'), cooking_club['cook'])
            message = "Uitnodiging kookclub\n{0}\nKosten per persoon: € {1}\n{2}".format(
                recipe['title'], cooking_club['cost'], cooking_club['invitation'])
            to_list = [cooking_club['email']]
            for participant in cooking_club['participants']:
                to_list.append(participant['email'])
            send_mail(subject, message, sender, to_list, fail_silently=True)
    context = {
        'recipe' : recipe
        }
    return HttpResponse(json.dumps(context), content_type='application/json')


