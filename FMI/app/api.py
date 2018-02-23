"""
Definition of api-views.
"""

from pandas import Series, DataFrame
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
#from django.http import JsonResponse
from django.template import RequestContext
from django.core.files import File
from datetime import datetime
import json
import FMI.settings
import app.models as models
import app.guide as guide
import app.conf as conf
import app.wb_excel as wb_excel
import app.workbooks as workbooks

from .scrape_ds import *

platformseekers = {
    'Fragrantica'           : (models.PerfumeSeekerView, "search_pi"),
    'Market Intelligence'   : (models.PostSeekerView, "search_mi"),
    'Cosmetica'             : (models.PageSeekerView, "search_si_sites"),
    'Feedly'                : (models.FeedlySeekerView, "search_feedly"),
    'Scent Emotion (Ingr)'  : (models.ScentemotionSeekerView, "search_scentemotion"),
    #'Scent Emotion (Studies)' : (models.StudiesSeekerView, "search_studies"),
    #'CI Surveys'            : (models.SurveySeekerView, "search_survey"),
    }


def storyboard_def(request):
    # the get can be called to first obtain the token, or it can be called to obtain the storyboard definition.
    # the token is used by the post method to return the changed storyboard definition
    if request.method == 'GET':
        workbook_name = request.GET.get('workbook_name', '')
        api_request = request.GET.get('api_request', '')
        if api_request == 'api_csrftoken':
            params = {
                'workbook_name' : workbook_name,
                }
            return render(request, 'app/api_csrftoken.html', {'params': params})
    if request.method == 'POST':
        workbook_name = request.POST.get('workbook_name', '')
        storyboards = json.loads(request.POST['storyboards'])
        charts = json.loads(request.POST['charts'])
        wb_excel.workbooks[workbook_name]['charts'] = charts

    storyboards = wb_excel.workbooks[workbook_name]['storyboards']
    charts = wb_excel.workbooks[workbook_name]['charts']
    context = {
        'workbook_name' : workbook_name,
        'storyboards'   : storyboards,
        'charts'        : charts,
        }
    json_results = json.dumps(context)
    return HttpResponse(json_results, content_type='application/json')


def site_menu(request):
    """Renders the guide page."""
    route_name = ''
    step_name = ''
    site_name = ''
    menu_name = ''
    view_name = ''
    benchmark = ''
    results = {}
    facets = {}
    default_methods = FMI.settings.CORS_ALLOW_METHODS
    if request.method == 'GET':
        route_name = request.GET.get('route_select', '')
        site_name = request.GET.get('site_select', '')
        menu_name = request.GET.get('menu_name', '')
        view_name = request.GET.get('view_name', '')
        benchmark = request.GET.get('benchmark', '')
        tile_facet_field = request.GET.get('tile_facet_field', '')
    if request.method == 'POST':
        route_name = request.POST.get('route_select', '')
        site_name = request.POST.get('site_select', '')
        menu_name = request.POST.get('menu_name', '')
        view_name = request.POST.get('view_name', '')
        benchmark = request.POST.get('benchmark', '')
        tile_facet_field = request.POST.get('tile_facet_field', '')
        #site_view = json.loads(request.POST['site_views'])

    if route_name != '':
        step_name = request.GET.get('step_name', '')
        route_steps = guide.routes[route_name][1]
        step_ix = 0
        # new route selected, start with the first step of this route
        if not ('guide_previous' in request.GET or 'guide_next' in request.GET):
            step_name = route_steps[0]
        else:
            for step in route_steps:
                if step == step_name:
                    break
                else:
                    step_ix = step_ix + 1
            if 'guide_previous' in request.GET:
                if step_ix > 0:
                    step_name = route_steps[step_ix - 1]
                else:
                    step_name = route_steps[0]
            if 'guide_next' in request.GET:
                if step_ix < len(route_steps)-1:
                    step_name = route_steps[step_ix + 1]
        if step_ix < len(route_steps)-1:
            results, facets = guide.route_step(request, route_name, step_name)
        else:      
            # destination reached, determine step_name                     
            step_name = guide.route_dest(request, route_name, step_name)
    else:
        if site_name != '':
            menu_name = request.GET.get('menu_name', '')
            view_name = request.GET.get('view_name', '')
            benchmark = request.GET.get('benchmark', '')
            tile_facet_field = request.GET.get('tile_facet_field', '')
            if site_name != '':
                results, facets = guide.site_menu(request, site_name, menu_name, view_name, tile_facet_field)

    context = {
            'site_name' : site_name,
            'menu_name' : menu_name,
            'view_name' : view_name,
            'benchmark' : benchmark,
            'sites'     : guide.sites,
            'site_views': guide.site_views
            }
    json_results = json.dumps(context)
    #json_results['Access-Control-Allow-Origin'] = '*'
    return HttpResponse(json_results, content_type='application/json')

def conf_edit(request):
    site_name = ''
    dashboard_name = ''
    chart_name = ''
    default_methods = FMI.settings.CORS_ALLOW_METHODS
    if request.method == 'GET':
        site_name = request.GET.get('site_select', '')
        dashboard_name = request.GET.get('dashboard_name', '')
        chart_name = request.GET.get('chart_name', '')
    if request.method == 'POST':
        site_name = request.POST.get('site_select', '')
        dashboard_name = request.POST.get('dashboard_name', '')
        chart_name = request.POST.get('chart_name', '')
        card_conf = json.loads(request.POST['card_conf'])

    context = {
            'site_select'   : site_name,
            'dashboard_name': dashboard_name,
            'chart_name'    : chart_name,
            'conf_edit'     : conf.conf_edit,
            }
    json_results = json.dumps(context)
    #json_results['Access-Control-Allow-Origin'] = '*'
    return HttpResponse(json_results, content_type='application/json')

def search_survey(request):

    pass

def platformsearch(request):
    results = {}
    keywords_q = request.GET['q']
    for dataset, seeker in platformseekers.items():
        seekerview = seeker[0]()
        using = seekerview.using
        index = seekerview.index
        #search = seekerview.document.search().index(index).using(using).extra(track_scores=True)
        search = seekerview.get_empty_search()
        if keywords_q:
            search = seekerview.get_search_query_type(search, keywords_q)
            results_count = search[0:0].execute().hits.total
            results[dataset] = {'count': results_count, 'url': seeker[1]}
    json_results = json.dumps(results)
    return HttpResponse(json_results, content_type='application/json')


def scrape_accords_api(request):
    accords_df_json = scrape_accords_json()
    return HttpResponse(accords_df_json, content_type='application/json')

def scrape_notes_api(request):
    notes_df_json = scrape_notes_json()
    return HttpResponse(notes_df_json, content_type='application/json')

def scrape_votes_api(request):
    votes_df_json = scrape_votes_json()
    return HttpResponse(votes_df_json, content_type='application/json')

def scrape_reviews_api(request):
    reviews_df_json = scrape_reviews_json()
    return HttpResponse(reviews_df_json, content_type='application/json')




