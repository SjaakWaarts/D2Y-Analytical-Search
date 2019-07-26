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
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
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
        'app/dhk/recipe.html',
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

