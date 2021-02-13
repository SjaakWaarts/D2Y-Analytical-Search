"""
Definition of views.
"""

from django.shortcuts import render, redirect
from django.template.context_processors import csrf
#from django.core.urlresolvers import reverse
# django2.0
from django.urls import reverse
from django.http import HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import seeker
import json
import urllib
from datetime import datetime, time
import FMI.settings
import app.elastic as elastic
import app.fragrantica as fragrantica
import app.sentiment as sentiment
import app.product as product
import app.market as market
import app.load as load
import app.cmis as cmis
import app.crawl as crawl
import app.survey as survey
import app.guide as guide
import app.aws as aws
import app.d2y_admin as d2y_admin
import app.wb_excel as wb_excel
import app.models as models
import app.survey
from .forms import *

models.SurveySeekerView.decoder = survey.seekerview_answer_value_decode

LOCAL_IPS = (
    '127.0.0.1'
)

def is_local_request(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip in LOCAL_IPS

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    if FMI.settings.site == 'DHK':
        return redirect('dhk:home')
    return render(
        request,
        'app/index.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year, 'keywords_q' : "" }
    )


def product_insight_view(request):
    """Renders the product_insight page."""
    if request.method == 'POST':
        if 'search_pi' in request.POST:
            return redirect('search_pi')

    return render(
        request,
        'app/product_insight.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )


def set_workbook(workbook_name):
    workbook = wb_excel.workbooks[workbook_name]
    es_index = workbook['es_index']
    models.ExcelDoc = seeker.mapping.document_from_index(es_index, using=models.client)
    models.ExcelSeekerView.document = models.ExcelDoc
    mapping = {'properties' : es_index['properties']}
    models.ExcelSeekerView.es_mapping = mapping
    models.ExcelSeekerView.index = es_index['index']
    if 'extra_columns' in es_index:
        models.ExcelSeekerView.extra_columns = es_index['extra_columns']
    if 'field_column_types' in es_index:
        models.ExcelSeekerView.field_column_types = es_index['field_column_types']
    if 'layout_template' in es_index:
        models.ExcelSeekerView.layout_template = es_index['layout_template']
    models.ExcelSeekerView.facets = es_index['facets']
    models.ExcelSeekerView.facets_keyword = es_index['facets_keyword']
    models.ExcelSeekerView.display = es_index['display']
    models.ExcelSeekerView.summary = es_index['summary']
    models.ExcelSeekerView.sumheader = es_index['sumheader']
    models.ExcelSeekerView.SUMMARY_URL = es_index['SUMMARY_URL']
    models.ExcelSeekerView.urlfields = es_index['urlfields']
    models.ExcelSeekerView.tabs = es_index['tabs']
    models.ExcelSeekerView.workbooks = wb_excel.workbooks
    url = workbook.get('url', 'search_excel')
    return url

def search_workbook(request):
    # prepare search_excel with the right
    user = request.user
    workbook_name = request.GET.get('workbook_name', '').strip()
    storyboard_name = request.GET.get('storyboard_name', 'initial').strip()
    dashboard_name = request.GET.get('dashboard_name', 'initial').strip()

    if workbook_name == 'tmlo':
        access =  user.has_perm('auth.edepot')

    url = set_workbook(workbook_name)
    url = reverse(url)

    kwargs={}
    kwargs['workbook_name'] = workbook_name
    kwargs['storyboard_name'] = storyboard_name
    kwargs['dashboard_name'] = dashboard_name
    for arg, arg_value in request.GET.items():
        kwargs[arg] = arg_value

    params = urllib.parse.urlencode(kwargs)
    #return redirect('search_excel')
    return HttpResponseRedirect(url + "?%s" % params)

def scent_emotion_view(request):
    if request.method == 'POST':
        if 'search_scentemotion' in request.POST:
            return redirect('search_scentemotion')
        elif 'search_studies' in request.POST:
            return redirect('search_studies')

    return render(
        request,
        'app/scent_emotion.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

def scrape_view(request):
    """Renders the scrape page."""
    if request.method == 'POST':
        form = scrape_form(request.POST)
        if form.is_valid():
            site_choices = form.cleaned_data['site_choices_field']
            scrape_choices = form.cleaned_data['scrape_choices_field']
            brand_name_field = form.cleaned_data['brand_name_field']
            if 'scrape' in form.data:
                models.scrape_li = fragrantica.fragrantica(site_choices, scrape_choices, brand_name_field)
                if not product.scrape_save(brand_name_field):
                    form.add_form_error("Could not save scrape results")
            if 'retrieve' in form.data:
                if not product.scrape_retrieve(brand_name_field):
                    form.add_form_error("Could not retrieve scrape results")
            if len(models.scrape_li) == 0:
                form.add_form_error("First retrieve or scrape the web for this brand")
            else:
                if 'explore' in form.data:
                    return render(request, 'app/scraperesults.html', {'brand': brand_name_field, 'scrape_li' : models.scrape_li } )
                if 'sentiment' in form.data:
                    sentiment.sentiment(brand_name_field)
                    if not product.scrape_save(brand_name_field):
                        form.add_form_error("Could not save scrape results")
                    return render(request, 'app/scraperesults.html', {'brand': brand_name_field, 'scrape_li' : models.scrape_li } )
            return render(request, 'app/scrape.html', {'site' : FMI.settings.site, 'form': form, 'scrape_li' : models.scrape_li } )
    else:
        form = scrape_form(initial={'site_choices_field':['fragrantica'],'scrape_choices_field':['accords','moods','notes']})

    return render(request, 'app/scrape.html', {'site' : FMI.settings.site, 'form': form, 'year':datetime.now().year})

def market_insight_view(request):
    "Renders the market insight page."
    if request.method == 'POST':
        if 'search_mi' in request.POST:
            return redirect('search_mi')
        elif 'search_feedly' in request.POST:
            return redirect('search_feedly')
        elif 'search_mail' in request.POST:
            return redirect('search_mail')
        elif 'search_si_sites' in request.POST:
            return redirect('search_si_sites')
    return render(
        request,
        'app/market_insight.html',
        {'site' : FMI.settings.site, 'es_hosts' : FMI.settings.ES_HOSTS, 'year':datetime.now().year}
    )

def guide_view(request):
    """Renders the guide page."""
    route_name = ''
    step_name = ''
    site_name = ''
    menu_name = ''
    view_name = ''
    benchmark = ''
    results = {}
    tiles_d = {}
    facets = {}
    if request.method == 'GET':
        route_name = request.GET.get('route_select', '')
        site_name = request.GET.get('site_select', '')
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
            'site' : FMI.settings.site,
            'insight_api' : FMI.settings.INSIGHT_API['url'],
            'facets'    : facets,
            'results'   : results,
            'site_name' : site_name,
            'menu_name' : menu_name,
            'view_name' : view_name,
            'benchmark' : benchmark,
            'sites'     : json.dumps(guide.sites),
            'site_views': json.dumps(guide.site_views)
        }

    return render(request, 'app/guide.html', context )


def aws_view(request):
    """Renders the facts page."""
    if request.method == 'POST':
        form = aws_form(request.POST)
        if form.is_valid():
            s3_choices = form.cleaned_data['s3_choices_field']
            bucket_objects = aws.s3_list_mails(s3_choices)
            return render(request, 'app/awsresults.html', {'bucket_objects' : bucket_objects} )
    else:
        form = aws_form(initial={'s3_choices_field':['deheerlijkekeuken']})

    return render(request, 'app/aws.html', {'site' : FMI.settings.site, 'form': form, 'year':datetime.now().year})

def consumer_insight_view(request):
    "Renders the consumer_insight page."
    if request.method == 'POST':
        if 'search_mi' in request.POST:
            return redirect('search_mi')
        elif 'search_feedly' in request.POST:
            return redirect('search_feedly')
        elif 'search_si_sites' in request.POST:
            return redirect('search_si_sites')
        elif 'search_pi' in request.POST:
            return redirect('search_pi')
        elif 'search_scentemotion' in request.POST:
            return redirect('search_scentemotion')
        elif 'search_survey' in request.POST:
            #return redirect('search_survey?tab=#storyboard_tab')
            #return redirect('search_survey', tab='#storyboard_tab')
            #return redirect('search_survey')
            #seekerview = models.SurveySeekerView()
            #request.method = 'GET'
            #request.path = '/search_survey'
            #request.path_info = '/search_survey'
            #seekerview.request = request
            #return seekerview.render()
            #url = reverse('search_survey', args=(), kwargs={'survey.keyword': '2015'})
            kwargs={}
            if 'workbook_name' in request.POST:
                kwargs['workbook_name'] = request.POST['workbook_name']
            if 'dashboard_name' in request.POST:
                kwargs['dashboard_name'] = request.POST['dashboard_name']
            url = reverse('search_survey')
            params = urllib.parse.urlencode(kwargs)
            return HttpResponseRedirect(url + "?%s" % params)
        elif 'search_studies' in request.POST:
            return redirect('search_studies')

    return render(request, 'app/consumer_insight.html', 
                  {'site' : FMI.settings.site, 'es_hosts' : FMI.settings.ES_HOSTS, 'year':datetime.now().year})


def platform_admin_view(request):
    "Renders the platform admin page."
    if request.method == 'POST':
        if 'scrape' in request.POST:
            return redirect('scrape')
        elif 'mail_tester' in request.POST:
            return redirect('product_elastic')
    return render(request, 'app/platform_admin.html', 
                  {'site' : FMI.settings.site, 'es_hosts' : FMI.settings.ES_HOSTS, 'year':datetime.now().year})

def crawl_view(request):
    """Renders the crawl page."""
    sections = {}
    if request.method == 'POST':
        form = crawl_form(request.POST)
        form.is_valid()
        # called from crawh.html
        if form.is_valid():
            from_dt = form.cleaned_data['from_dt']
            nrpages = form.cleaned_data['nrpages_field']
            site_choices = form.cleaned_data['site_choices_field']
            scrape_choices = form.cleaned_data['scrape_choices_field']
            rss_field = form.cleaned_data['rss_field']
            brand_name = form.cleaned_data['brand_name_field']
            brand_variant = form.cleaned_data['brand_variant_field']
            perfume_code = form.cleaned_data['perfume_code_field'].lower()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if from_dt == None:
                today = datetime.now()
                from_dt = datetime(today.year-1, 1, 1).date()
            # Crawl BLOG Sites
            if 'crawl_si_sites' in form.data:
                for site_choice in site_choices:
                    if site_choice == 'apf':
                        crawl.crawl_apf(from_dt, scrape_choices, nrpages)
                    elif site_choice == 'cosmetics':
                        crawl.crawl_cosmetic(from_dt, scrape_choices, nrpages)
                    else:
                        crawl.crawl_si_site(from_dt, site_choice, nrpages)
            # Crawl Market Intelligence Sites
            if 'crawl_feedly' in form.data:
                if not crawl.crawl_feedly(from_dt, rss_field):
                     form.add_form_error("Could not retrieve feedly data, expired")
            elif 'crawl_mi' in form.data:
                if not market.index_posts(from_dt, username, password):
                    form.add_form_error("Could not index category posts")
            # Crawl Product Intelligence Sites
            if 'crawl_pi' in form.data and 'pi_site_choices_field' in request.POST:
                pi_site_choices = request.POST['pi_site_choices_field']
                if perfume_code == '':
                    form.add_form_error("Specify a product code")
                else:
                    if pi_site_choices == 'fragrantica':
                        success = product.crawl_fragrantica(from_dt, brand_name, brand_variant, perfume_code)
                    elif pi_site_choices == 'amazon':
                        success = product.crawl_amazon(from_dt, brand_name, brand_variant, perfume_code)
                    elif pi_site_choices == 'basenotes':
                        success = product.crawl_basenotes(from_dt, brand_name, brand_variant, perfume_code)
                    if not success:
                        form.add_form_error("Could not save product data")
            if 'retrieve_pi' in form.data and 'pi_site_choices_field' in request.POST:
                pi_site_choices = request.POST['pi_site_choices_field']
                if perfume_code == '':
                    form.add_form_error("Specify a product code")
                else:
                    if pi_site_choices == 'fragrantica':
                        success = product.retrieve_fragrantica(perfume_code)
                    elif pi_site_choices == 'amazon':
                        success = product.retrieve_amazon(perfume_code)
                    if pi_site_choices == 'basenotes':
                        success = product.retrieve_basenotes(perfume_code)
                    if not success:
                        form.add_form_error("Could not save product data")
            if 'return_survey' in form.data:
                pass
            return render(
                request,
                'app/crawl.html',
                {'site' : FMI.settings.site, 'form': form, 'es_hosts' : FMI.settings.ES_HOSTS, 'sections' : sections, 'scrape_li' : models.scrape_li }
            )
    else:
        form = crawl_form(initial={'scrape_choices_field':['product', 'blog'], 'excel_choices_field':['recreate']})
        if 'crawl_pi' in request.GET:
            sections['crawl_mi'] = 0
            sections['crawl_feedly'] = 0
            sections['crawl_si_sites'] = 0
            sections['crawl_pi'] = 1
        else:
            sections['crawl_mi'] = 1
            sections['crawl_feedly'] = 1
            sections['crawl_si_sites'] = 1
            sections['crawl_pi'] = 1

    return render(
        request,
        'app/crawl.html',
        {'site' : FMI.settings.site, 'form': form, 'es_hosts' : FMI.settings.ES_HOSTS, 'sections' : sections, 'year':datetime.now().year})


def load_view(request):
    """Renders the load page."""
    if request.method == 'POST':
        form = load_form(request.POST)
        form.is_valid()
        ci_filename = form.cleaned_data['ci_filename_field']
        cimap_filename = form.cleaned_data['cimap_filename_field']
        # called form loadresults.html
        if 'load_survey' in form.data:
            load.load_survey(request, ci_filename, cimap_filename)
        # called from load.html
        if form.is_valid():
            cft_filename = form.cleaned_data['cft_filename_field']
            recipes_foldername = form.cleaned_data['recipes_foldername_field']
            excel_choices = form.cleaned_data['excel_choices_field']
            excel_filename = form.cleaned_data['excel_filename_field']
            excelmap_filename = form.cleaned_data['excelmap_filename_field']
            cmis_choices = form.cleaned_data['cmis_choices_field']
            cmis_foldername = form.cleaned_data['cmis_foldername_field']
            cmis_objtype = form.cleaned_data['cmis_objtype_field']
            email_choices = form.cleaned_data['email_choices_field']
            email_address = form.cleaned_data['email_address_field']
            email_password = form.cleaned_data['email_password_field']
            index_doc_name = form.cleaned_data['index_doc_name_field']
            ci_filename = form.cleaned_data['ci_filename_field']
            cimap_filename = form.cleaned_data['cimap_filename_field']
            if 'load_scentemotion' in form.data:
                load.load_scentemotion(cft_filename)
            if 'load_recipes' in form.data:
                load.load_recipes(recipes_foldername)
            if 'load_excel' in form.data:
                if not load.load_excel(excel_filename, excelmap_filename, excel_choices, index_doc_name):
                    form.add_form_error("Could not retrieve or index excel file")
            if 'load_cmis' in form.data:
                if not cmis.load_cmis(cmis_foldername, cmis_objtype, cmis_choices):
                    form.add_form_error("Could not retrieve or index excel file")
            if 'load_mail' in form.data:
                if not load.load_mail(email_choices, email_address, email_password):
                    form.add_form_error("Could not retrieve mailbox")
            if 'map_survey' in form.data:
                field_map, col_map, header_map = load.map_survey(ci_filename, cimap_filename)
                qa = {}
                for question, answers in survey.qa.items():
                    qa[question] = list(answers.keys())
                context = {
                    'form'          : form,
                    'col_map'       : col_map,
                    'header_map'    : header_map,
                    'qa'            : qa,
                    }
                return render(request, 'app/loadresults.html', context )
            if 'return_survey' in form.data:
                pass
            return render(request,
                          'app/load.html',
                          {'site' : FMI.settings.site, 'form': form, 'es_hosts' : FMI.settings.ES_HOSTS, 'year':datetime.now().year} )
    else:
        form = load_form(initial={'excel_choices_field':['recreate'], 'email_choices_field':['imap']})

    return render(
        request,
        'app/load.html',
        {'site' : FMI.settings.site, 'form': form, 'es_hosts' : FMI.settings.ES_HOSTS, 'year':datetime.now().year})

def d2y_admin_view(request):
    """Renders the Admin Index page."""
    if request.method == 'POST':
        form = d2y_admin_form(request.POST)
        if form.is_valid():
            index_choices = form.cleaned_data['index_choices_field']
            excel_filename = form.cleaned_data['excel_filename_field']
            opml_filename = form.cleaned_data['opml_filename_field']
            auth_group_choices = form.cleaned_data['auth_group_choices_field']
            auth_permission_choices = form.cleaned_data['auth_permission_choices_field']
            keyword_filename = form.cleaned_data['keyword_filename_field']
            if 'index_elastic' in form.data:
                d2y_admin.create_index_elastic(index_choices, excel_filename)
            elif 'analyzer' in form.data:
                d2y_admin.create_analyzer(index_choices)
            if 'export_opml' in form.data:
                if not d2y_admin.export_opml(index_choices, opml_filename):
                    form.add_form_error("Could not export OPML")
            elif 'import_opml' in form.data:
                if not d2y_admin.import_opml(index_choices, opml_filename):
                    form.add_form_error("Could not import OPML")
            elif 'keywords' in form.data:
                if not d2y_admin.read_keywords(index_choices, keyword_filename):
                    form.add_form_error("Could not read keywords file")
            if 'auth_groups' in form.data:
                d2y_admin.auth_groups(auth_group_choices)
            if 'auth_permissions' in form.data:
                d2y_admin.auth_permissions(auth_permission_choices)
            if 'auth_hasperm' in form.data:
                d2y_admin.auth_hasperm(auth_group_choices, auth_permission_choices)
            return render(request, 'app/d2y_admin.html', {'form': form })
    else:
        form = d2y_admin_form(initial={'index_choices_field':['cosmetic']})

    return render(request, 'app/d2y_admin.html', {'site' : FMI.settings.site, 'form': form, 'year':datetime.now().year})

def elastic_view(request):
    """Renders the elastic page."""
    assert isinstance(request, HttpRequest)
    elastic.elastic_bank()
#    elastic.elastic_seeker1()
    elastic.elastic_seeker2()
    elastic.elastic_review()
    elastic.sharepoint_mi()
    return render(
        request,
        'app/index.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )


def autocomplete_view(request):
    query = request.GET.get('term', '')
#    resp = models.client.suggest(
#        index='review',
#        body={                                                                                                                                          
#            'perfume': {
#               "text": query,
#               "completion": {
#                   "field": 'perfume',
#               }
#            }
#        }
#    )
    s = Search(using=models.client, index = "review")
    s = s.filter("term", perfume=query)
    resp = s.execute()

    perfumes = []
    for hit in resp:
        perfumes.append(hit.perfume)
    data = json.dumps(perfumes)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def mail_tester_view(request):
    recipe = {'title' : "Test mail"}
    cooking_club = {}
    return render(
        request, 'dhk_app/cooking_club_mail.html',
                  {'recipe': recipe, 'cooking_club': cooking_club})

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )





