
import json
from datetime import datetime, time
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
import seeker.esm as esm
import FMI.settings
from FMI.settings import BASE_DIR, ES_HOSTS

# Create your views here.


def club_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/club.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

def calendar_items_api(request):
    calendar_items = []
    # Set up elastic search query
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    search_filters = search_q["query"]["bool"]["filter"]
    search_aggs = search_q["aggs"]

    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    hits = hits.get('hits', {})
    for hit in hits:
        recipe = hit.get('_source', {})
        for cooking_club in recipe.get('cooking_clubs', {}):
            calendar_item = {}
            calendar_item['id'] = hit['_id']
            calendar_item['title'] = cooking_club['invitation']
            calendar_item['start'] = cooking_club['cooking_date']
            calendar_item['end'] = calendar_item['start']
            calendar_item['extendedProps'] = cooking_club
            calendar_items.append(calendar_item)

    return HttpResponse(json.dumps(calendar_items), content_type='application/json')



