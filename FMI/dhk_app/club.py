
import json
from datetime import datetime, time
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import ensure_csrf_cookie
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

# prevent CsrfViewMiddleware from reading the POST stream
#@csrf_exempt
@requires_csrf_token
def get_cooking_clubs(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    filter_facets = json_data.get('filter_facets', None)
    sort_facets = json_data.get('sort_facets', None)
    pager = json_data.get('pager', None)
    q = ""
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    ##
    # Workbook
    ##
    workbook = {
        'facets': {
            'author': {
                'label': None, 'field': 'author', 'has_keyword': True, 'size' : "1", 'multiple' : False,
                'nested': None, 'type': 'terms', 'value' : None},
            'published_date': {
                'label': None, 'field': 'published_date', 'has_keyword': False,
                'nested': None, 'type': 'date', 'value' : None},
            'title': {
                'label': None, 'field': 'title', 'has_keyword': False,
                'nested': None, 'type': 'text', 'value' : None},
            'cook': {
                'label': None, 'field': 'cooking_clubs.cook', 'has_keyword': True,
                'nested': 'cooking_clubs', 'type': 'terms', 'value' : None},
            'categories': {
                'label': None, 'field': 'categories', 'has_keyword': True,
                'nested': None, 'type': 'terms', 'value' : None},
            'cooking_date': {
                'label': None, 'field': 'cooking_clubs.cooking_date', 'has_keyword': False,
                'nested': 'cooking_clubs', 'type': 'period', 'value' : {'start': None, 'end': None}},
        },
        'filters': ['author', 'published_date', 'title', 'cook', 'categories', 'cooking_date'],
        'charts': {},
        'columns': ['author', 'title', 'published_date', 'cook', 'categories', 'cooking_date'],
        'pager': {'nr_hits': 0, 'page_size': 10},
        'sort': [],
        'table': []
    }
    ##
    # Add Aggs
    ##
    search_aggs = search_q["aggs"]
    for facet, facet_conf in workbook['facets'].items():
        if facet in workbook['filters'] and facet_conf['type'] == 'terms':
            field = facet_conf['field']
            if facet_conf['has_keyword']:
                field = field + '.keyword'
            nested = facet_conf['nested']
            search_aggs[facet] = {'terms': {"field": field}}
            terms_agg = {'terms': {"field": field}}
            search_aggs[facet] = esm.add_agg_nesting(field, nested, terms_agg)
    ##
    # Add Filters
    ##
    cooking_date_filter = filter_facets.get('cooking_date', {'start': None, 'end': None})
    if cooking_date_filter.get('start', None) is None and cooking_date_filter.get('end', None) is None:
        year = datetime.today().year
        month = datetime.today().month
        startdt = "{0}-{1:02d}-01".format(year, month)
        month = month + 3
        if month > 12:
            year = year + 1
            month = 3
        enddt = "{0}-{1:02d}-01".format(year, month)
        filter_facets['cooking_date'] = {'start' : startdt, 'end' : enddt}
    search_filters = search_q["query"]["bool"]["filter"]
    search_queries = search_q["query"]["bool"]["must"]
    esm.add_search_filter(search_q, filter_facets, workbook)
    for facet_name in workbook['filters']:
        facet_conf = workbook['facets'][facet_name]
        if facet_name in filter_facets:
            if facet_conf['type'] == 'terms':
                facet_conf['value'] = filter_facets[facet_name]
            if facet_conf['type'] == 'text':
                facet_conf['value'] = filter_facets[facet_name]
            if facet_conf['type'] == 'date':
                facet_conf['value'] = filter_facets[facet_name]
            if facet_conf['type'] == 'period':
                facet_conf['value'] = filter_facets[facet_name]
    ##
    # Add Sorts
    ##
    if not sort_facets and workbook['sort']:
        sort_facets = workbook['sort']
    for facet, facet_conf in workbook['facets'].items():
        if facet in sort_facets:
            field = facet_conf['field']
            if facet_conf['has_keyword']:
                field = field + '.keyword'
            nested = facet_conf['nested']
            order = sort_facets[facet]
            search_q["sort"].append({field: {"order": order}})
    ##
    # Add Search
    ##
    if q is not None and q != "":
        search_q["query"]["bool"]["must"].append({"query_string": {
            "query": q, "default_operator": "AND", "fields": ["Identificatiekenmerk", "Namen"]}})
    ##
    # Add Page
    ##
    search_q["from"] = (pager['page_nr'] - 1) * pager['page_size']
    search_q["size"] = pager['page_size']
    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    pager['nr_hits'] = hits.get('total', 0)
    aggs = results.get('aggregations', [])
    ##
    # Parse Aggs into Filter values and Charts that contain Aggs
    ##
    for facet, facet_conf in workbook['facets'].items():
        if facet in workbook['filters']:
            if facet in aggs:
                field = facet_conf['field']
                if facet_conf['has_keyword']:
                    field = field + '.keyword'
                nested = facet_conf['nested']
                buckets, totals = esm.get_buckets_nesting(field, nested, aggs[facet])
                workbook['facets'][facet]['buckets'] = buckets
    context = {
        'workbook' : workbook,
        'pager' : pager,
        'hits'  : hits,
        'aggs'  : aggs
        }
    return HttpResponse(json.dumps(context), content_type='application/json')
