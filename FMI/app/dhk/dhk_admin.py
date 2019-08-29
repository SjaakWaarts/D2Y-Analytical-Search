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
from slugify import slugify
from io import BytesIO
import zipfile
import docx
from docx.table import _Cell, Table
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import ensure_csrf_cookie
import seeker.esm as esm
import FMI.settings
from FMI.settings import BASE_DIR, ES_HOSTS

def dhk_admin_view(request):
    """Renders dhk page."""
    if request.method == 'GET':
        return render(
            request,
            'app/dhk/dhk_admin.html',
            {'site' : FMI.settings.site, 'year':datetime.now().year}
        )
    else:
        return HttpResponse({'status' : 'OK'}, content_type='application/json')


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


# prevent CsrfViewMiddleware from reading the POST stream
#@csrf_exempt
@requires_csrf_token
def get_uploaded_files(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    json_data = json.loads(request.body)
    pager = json_data.get('pager', None)
    es_host = ES_HOSTS[0]
    s, search_q = esm.setup_search()
    results = esm.search_query(es_host, 'recipes', search_q)
    results = json.loads(results.text)
    hits = results.get('hits', {})
    context = {
        'pager' : pager,
        'hits'  : hits,
        }
    return HttpResponse(json.dumps(context), content_type='application/json')

def has_image(par):
    """get all of the images in a paragraph 
    :param par: a paragraph object from docx
    :return: a list of r:embed 
    """
    ids = []
    root = ET.fromstring(par._p.xml)
    namespace = {
             'a':"http://schemas.openxmlformats.org/drawingml/2006/main", \
             'r':"http://schemas.openxmlformats.org/officeDocument/2006/relationships", \
             'wp':"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"}

    inlines = root.findall('.//wp:inline',namespace)
    for inline in inlines:
        imgs = inline.findall('.//a:blip', namespace)
        for img in imgs:     
            id = img.attrib['{{{0}}}embed'.format(namespace['r'])]
        ids.append(id)

def iter_block_items(parent):
    if isinstance(parent, docx.document.Document):
        parent_elm = parent.element.body
    elif isinstance(parent, docx.table._Cell):
        parent_elm = parent._tc
    elif isinstance(parent, docx.table._Row):
        parent_elm = parent._tr
    else:
        raise ValueError("something's not right")
    for child in parent_elm.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            yield docx.text.paragraph.Paragraph(child, parent)
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            yield Table(child, parent)

def load_recipe(recipe_fullname, recipe_basename, namelist):
    es_host = ES_HOSTS[0]
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    index_name = 'recipes'
    doc_type = 'recipes'
    url = "http://" + host + ":9200/" + index_name

    recipe = {}
    recipe['id'] = recipe_basename
    recipe['title'] = recipe_basename
    #recipe['url'] = 'http://www.deheerlijkekeuken.nl/' + recipe_basename
    recipe['excerpt'] = ""
    recipe['description'] = []
    recipe['categories'] = []
    recipe['tags'] = []
    recipe['images'] = []
    recipe['courses'] = []

    image_type = "featured"
    for name in namelist:
        if name.startswith('word/media/'):
            image_location = os.path.join('data', 'dhk', 'recipes', recipe_basename, 'word', 'media', name[11:])
            image = {'type' : image_type, 'location' : image_location}
            recipe['images'].append(image)
            image_type = "image"

    mode = 'dish'
    doc = docx.Document(recipe_fullname)
    core_properties = doc.core_properties
    recipe['author'] = core_properties.author
    recipe['published_date'] = core_properties.created.strftime('%Y-%m-%d')
    for block in iter_block_items(doc):
        if isinstance(block, docx.text.paragraph.Paragraph):
            para = block
            if len(para.text) > 0:
                style_name = para.style.name
                if style_name == 'Course':
                    mode = 'recipe'
                    course = {}
                    course['title'] = para.text
                    course['ingredients'] = []
                    course['instructions'] = []
                    recipe['courses'].append(course)
                if mode == 'dish':
                    if style_name == 'Excerpt':
                        recipe['excerpt']= recipe['excerpt'] + para.text
                    if style_name == 'Categories':
                        pattern = re.compile("^\s+|\s*,\s*|\s+$")
                        categories_text = para.text.split(':')[1]
                        recipe['categories'].extend([x for x in pattern.split(categories_text) if x])
                    if style_name == 'Tags':
                        pattern = re.compile("^\s+|\s*,\s*|\s+$")
                        tags_text = para.text.split(':')[1]
                        recipe['tags'].extend([x for x in pattern.split(tags_text) if x])
                if mode == 'recipe':
                    if style_name == 'Recept':
                        course['instructions'].append({'instruction' : para.text})
                recipe['description'].append(para.text)
        elif isinstance(block, Table):
            table = block
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if len(para.text) > 0:
                            style_name = para.style.name
                            if style_name == 'Ingredients':
                                course['ingredients'].append({'ingredient' : para.text})
                            recipe['description'].append(para.text)
    for image in doc.inline_shapes:
        pass
    data = json.dumps(recipe)
    r = requests.put(url + "/" + doc_type + "/" + recipe_basename, headers=headers, data=data)
    print("load_recipe: written recipe with id", recipe_basename)


def ingest_recipe(recipe_fullname):
    recipe_filename = os.path.basename(recipe_fullname)
    recipe_basename, recipe_ext = os.path.splitext(recipe_filename)
    recipe_basename = slugify(recipe_basename)
    zip_filename = recipe_basename + '.zip'
    zip_fullname = os.path.join(BASE_DIR, 'data', 'dhk', 'recipes', zip_filename)
    shutil.copy(recipe_fullname, zip_fullname)
    zip_dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'recipes', recipe_basename)
    zip_ref = zipfile.ZipFile(zip_fullname, 'r')
    namelist = zip_ref.namelist()
    zip_ref.extractall(zip_dirname)
    zip_ref.close()
    load_recipe(recipe_fullname, recipe_basename, namelist)
    os.remove(recipe_fullname)
    os.remove(zip_fullname)

def upload_file(request):
    request_file = request.FILES['file']
    dropdown_filename = request_file.name
    dropdown_file_handler = request_file.file
    dropdown_basename, dropdown_ext = os.path.splitext(dropdown_filename)
    dropdown_basename = slugify(dropdown_basename)
    dropdown_filename = dropdown_basename + dropdown_ext
    dropdown_fullname = os.path.join(BASE_DIR, 'data', 'dhk', 'recipes', dropdown_filename)
    buffer_file = BytesIO(dropdown_file_handler.read())
    # Make sure we start copying from the beginning.
    buffer_file.seek(0)
    try:
        with open(dropdown_fullname, 'wb') as output_file:
            shutil.copyfileobj(buffer_file, output_file)
    except IOError as e:
        return False
    if dropdown_ext == '.zip':
        zip_dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'recipes', dropdown_basename)
        zip_ref = zipfile.ZipFile(dropdown_fullname, 'r')
        zip_ref.extractall(zip_dirname)
        zip_ref.close()
    elif dropdown_ext == '.docx':
        ingest_recipe(dropdown_fullname)

    return HttpResponse( {'succes': 'Bestand succesvol geüpload'}, content_type='application/json')


def stream_file(request):
    location = request.GET.get('location', None)
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
        return response
    else:
        response = HttpResponse(content_type="image/jpeg")
        return response

