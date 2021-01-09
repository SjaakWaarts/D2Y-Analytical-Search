"""
Definition of api-views.
"""

import sys
import io
import requests
#import magic
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
from FMI.settings import BASE_DIR, ES_HOSTS

from .scrape_ds import *

types_map = {
    '.a': 'application/octet-stream',
    '.ai': 'application/postscript',
    '.aif': 'audio/x-aiff',
    '.aifc': 'audio/x-aiff',
    '.aiff': 'audio/x-aiff',
    '.au': 'audio/basic',
    '.avi': 'video/x-msvideo',
    '.bat': 'text/plain',
    '.bcpio': 'application/x-bcpio',
    '.bin': 'application/octet-stream',
    '.bmp': 'image/bmp',
    '.c': 'text/plain',
    '.cdf': 'application/x-netcdf',
    '.cpio': 'application/x-cpio',
    '.csh': 'application/x-csh',
    '.css': 'text/css',
    '.csv': 'text/csv',
    '.dll': 'application/octet-stream',
    '.doc': 'application/msword',
    '.dot': 'application/msword',
    '.dvi': 'application/x-dvi',
    '.eml': 'message/rfc822',
    '.eps': 'application/postscript',
    '.etx': 'text/x-setext',
    '.exe': 'application/octet-stream',
    '.gif': 'image/gif',
    '.gtar': 'application/x-gtar',
    '.h': 'text/plain',
    '.hdf': 'application/x-hdf',
    '.htm': 'text/html',
    '.html': 'text/html',
    '.ico': 'image/vnd.microsoft.icon',
    '.ief': 'image/ief',
    '.jpe': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.ksh': 'text/plain',
    '.latex': 'application/x-latex',
    '.m1v': 'video/mpeg',
    '.m3u': 'application/vnd.apple.mpegurl',
    '.m3u8': 'application/vnd.apple.mpegurl',
    '.man': 'application/x-troff-man',
    '.me': 'application/x-troff-me',
    '.mht': 'message/rfc822',
    '.mhtml': 'message/rfc822',
    '.mif': 'application/x-mif',
    '.mjs': 'application/javascript',
    '.mov': 'video/quicktime',
    '.movie': 'video/x-sgi-movie',
    '.mp2': 'audio/mpeg',
    '.mp3': 'audio/mpeg',
    '.mp4': 'video/mp4',
    '.mpa': 'video/mpeg',
    '.mpe': 'video/mpeg',
    '.mpeg': 'video/mpeg',
    '.mpg': 'video/mpeg',
    '.ms': 'application/x-troff-ms',
    '.nc': 'application/x-netcdf',
    '.nws': 'message/rfc822',
    '.o': 'application/octet-stream',
    '.obj': 'application/octet-stream',
    '.oda': 'application/oda',
    '.p12': 'application/x-pkcs12',
    '.p7c': 'application/pkcs7-mime',
    '.pbm': 'image/x-portable-bitmap',
    '.pdf': 'application/pdf',
    '.pfx': 'application/x-pkcs12',
    '.pgm': 'image/x-portable-graymap',
    '.pl': 'text/plain',
    '.png': 'image/png',
    '.pnm': 'image/x-portable-anymap',
    '.pot': 'application/vnd.ms-powerpoint',
    '.ppa': 'application/vnd.ms-powerpoint',
    '.ppm': 'image/x-portable-pixmap',
    '.pps': 'application/vnd.ms-powerpoint',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.ps': 'application/postscript',
    '.pwz': 'application/vnd.ms-powerpoint',
    '.py': 'text/x-python',
    '.pyc': 'application/x-python-code',
    '.pyo': 'application/x-python-code',
    '.qt': 'video/quicktime',
    '.ra': 'audio/x-pn-realaudio',
    '.ram': 'application/x-pn-realaudio',
    '.ras': 'image/x-cmu-raster',
    '.rdf': 'application/xml',
    '.rgb': 'image/x-rgb',
    '.roff': 'application/x-troff',
    '.rtx': 'text/richtext',
    '.sgm': 'text/x-sgml',
    '.sgml': 'text/x-sgml',
    '.sh': 'application/x-sh',
    '.shar': 'application/x-shar',
    '.snd': 'audio/basic',
    '.so': 'application/octet-stream',
    '.src': 'application/x-wais-source',
    '.sv4cpio': 'application/x-sv4cpio',
    '.sv4crc': 'application/x-sv4crc',
    '.svg': 'image/svg+xml',
    '.swf': 'application/x-shockwave-flash',
    '.t': 'application/x-troff',
    '.tar': 'application/x-tar',
    '.tcl': 'application/x-tcl',
    '.tex': 'application/x-tex',
    '.texi': 'application/x-texinfo',
    '.texinfo': 'application/x-texinfo',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.tr': 'application/x-troff',
    '.tsv': 'text/tab-separated-values',
    '.txt': 'text/plain',
    '.ustar': 'application/x-ustar',
    '.vcf': 'text/x-vcard',
    '.wav': 'audio/x-wav',
    '.webm': 'video/webm',
    '.wiz': 'application/msword',
    '.wsdl': 'application/xml',
    '.xbm': 'image/x-xbitmap',
    '.xlb': 'application/vnd.ms-excel',
    '.xls': 'application/vnd.ms-excel',
    '.xml': 'text/xml',
    '.xpdl': 'application/xml',
    '.xpm': 'image/x-xpixmap',
    '.xsl': 'application/xml',
    '.xwd': 'image/x-xwindowdump',
    '.zip': 'application/zip',
}

def get_ext(content_type):
    ext = ""
    for ex, ct in types_map.items():
        if ct == content_type:
            ext = ex
            break
    return ext

platformseekers = {
    'Fragrantica'           : (models.PerfumeSeekerView, "search_pi"),
    'Market Intelligence'   : (models.PostSeekerView, "search_mi"),
    'Cosmetica'             : (models.PageSeekerView, "search_si_sites"),
    'Feedly'                : (models.FeedlySeekerView, "search_feedly"),
    'Scent Emotion (Ingr)'  : (models.ScentemotionSeekerView, "search_scentemotion"),
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

#def get_PDF(self):
#    # url_check = r'^(http:\/\/(?:archive\.divault\.(com|local)|dv-cl01\.divault\.local):\d+\/\w+)(?:\?hashtype=\w+&hash=\w+)?'
#    # safe_url = re.match(url_check, request.GET.get('url', None))
#    # if not safe_url:
#    #    raise PermissionDenied
#    # url = safe_url.group(1).replace('com', 'local')
#    basename = self.request.GET.get('basename', None)
#    url = self.request.GET.get('url', None)
#    file_url = self.request.GET.get('file_url', None)
#    try:
#        pdf = urllib.request.urlopen(url)
#    except urllib.error.URLError as e:
#        logger.error('Failed to open pdf for {}.'.format(url),
#                        extra={
#                            'organisation': self.request.user.organisation.code,
#                            'user': self.request.user.username,
#                            'id': basename, 'statuscode': 0})
#        response = render(self.request, 'website/modal-popup/modal_error.html',
#                            {'error_message': e.reason, 'error_type': 'URLError'})
#        return response
#    # response = HttpResponse(pdf.read(), content_type='application/pdf')
#    # response['content-disposition'] = 'inline;filename=' + basename
#    response = Response(pdf.read(), content_type='application/pdf')
#    response.content_disposition = 'inline;filename=' + basename
#    return response

def stream_file(request):
    location = request.GET.get('location', None)
    # for media.deheerlijkekeuken.nl use the redirect approach since Chrome doesn't support mixed content (http and https).
    # a static website from S3 doesn't support https
    if location[:4] == 'http':
        response = requests.get(location)
        content_type = response.headers['Content-Type']
        bytes_io = io.BytesIO()
        bytes_io.write(response.content)
        bytes_io.seek(0)
        response = HttpResponse(bytes_io, content_type=content_type)
    else:
        if sys.platform[0:3] == "win":
            location = location.replace('/', '\\')
        else:
            location = location.replace('\\', '/')
        filename = os.path.join(BASE_DIR, location)
        if os.path.isfile(filename):
            #mime = magic.Magic(mime=True)
            #content_type = mime.from_file(filename)
            splitext = os.path.splitext(filename)
            basename = os.path.basename(filename)
            content_type = types_map[splitext[1]]
            with open(filename, "rb") as f:
                response = HttpResponse(f.read(), content_type=content_type)
            #response._headers['Content-Disposition'] = "attachment; filename=" + basename
        else:
            response = HttpResponse(content_type="image/jpeg")
    return response



