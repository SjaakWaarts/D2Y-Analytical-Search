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

def get_uploaded_files(request):
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    hits = hits['hits']
    zip_list = []
    cnt = 1
    for hit in hits:
        file_info = {
            'id': cnt,
            'name': hit['_id'],
            'status': [],
            'latest_status': 200,
            'approved': False,
            'imode': "name",
            'aggrs' : []
            }
        zip_list.append(file_info)
        cnt = cnt + 1
    zip_list_json = json.dumps(zip_list)
    return HttpResponse(zip_list_json, content_type='application/json')


def recipe_view(request):
    """Renders dhk page."""
    return render(
        request,
        'app/dhk/recipe.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

