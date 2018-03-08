from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse, QueryDict, Http404
from django.shortcuts import render, redirect
from django.template import loader, Context, RequestContext
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.generic import View
from django.core.files import File
import glob, os
from elasticsearch_dsl.utils import AttrList, AttrDict
#from seeker.templatetags.seeker import seeker_format
from app.templatetags.seeker import seeker_format
from FMI.settings import BASE_DIR
from seeker.summary import get_ngrams, clean_input
import seeker.models
import seeker.dashboard
import seeker.cards
import seeker.facets
from .mapping import DEFAULT_ANALYZER
import collections
from collections import OrderedDict
import elasticsearch_dsl as dsl
import inspect
import six
import urllib
import json
import re
import datetime

import pandas as pd

def date_value_format(value):
    if type(value) == datetime.datetime:
        return value.strftime("%Y-%m-%d")
    else:
        return value

class Column (object):
    """
    """

    view = None
    visible = False
    summary = False
    sumheader = False

    def __init__(self, field, label=None, sort=None, value_format=None, template=None, header=None, export=True, highlight=None):
        self.field = field
        self.label = label if label is not None else field.replace('_', ' ').replace('.raw', '').capitalize()
        self.sort = sort
        self.template = template
        self.value_format = value_format
        self.header_html = escape(self.label) if header is None else header
        self.export = export
        self.highlight = highlight

    def __str__(self):
        return self.label

    def __repr__(self):
        return 'Column(%s)' % self.field

    def bind(self, view, visible, summary, sumheader):
        self.view = view
        self.visible = visible
        self.summary = summary
        self.sumheader = sumheader
        search_templates = []
        if self.template:
            search_templates.append(self.template)
        for cls in inspect.getmro(view.document):
            if issubclass(cls, dsl.DocType):
                search_templates.append('app/seeker/%s/%s.html' % (cls._doc_type.name, self.field))
        search_templates.append('app/seeker/column.html')
        self.template = loader.select_template(search_templates)
        return self

    def header(self):
        cls = '%s_%s' % (self.view.document._doc_type.name, self.field.replace('.', '_'))
        if not self.sort:
            return mark_safe('<th class="%s">%s</th>' % (cls, self.header_html))
        q = self.view.request.GET.copy()
        field = q.get('s', '')
        sort = None
        cls += ' sort'
        if field.lstrip('-') == self.field:
            # If the current sort field is this field, give it a class a change direction.
            sort = 'Descending' if field.startswith('-') else 'Ascending'
            cls += ' desc' if field.startswith('-') else ' asc'
            d = '' if field.startswith('-') else '-'
            q['s'] = '%s%s' % (d, self.field)
        else:
            q['s'] = self.field
        next_sort = 'descending' if sort == 'Ascending' else 'ascending'
        sr_label = (' <span class="sr-only">(%s)</span>' % sort) if sort else ''
        html = '<th class="%s"><a href="?%s" title="Click to sort %s" data-sort="%s">%s%s</a></th>' % (cls, q.urlencode(), next_sort, q['s'], self.header_html, sr_label)
        return mark_safe(html)

    def context(self, result, **kwargs):
        return kwargs

    def render(self, result, facets, **kwargs):
        value = getattr(result, self.field, None)
        if self.value_format:
            value = self.value_format(value)
        try:
            if '*' in self.highlight:
                # If highlighting was requested for multiple fields, grab any matching fields as a dictionary.
                r = self.highlight.replace('*', r'\w+').replace('.', r'\.')
                highlight = {f: result.meta.highlight[f] for f in result.meta.highlight if re.match(r, f)}
            else:
                highlight = result.meta.highlight[self.highlight]
        except:
            highlight = []

        # for each found hit, the url attribute is filled with the link pointing to the corresponding article
        # it is possible to overwrite this url on field level (urlfields)
        url = ""
        if self.field in self.view.sumheader:
            url = result.url
        if self.field in self.view.urlfields:
            if value:
                url = self.view.urlfields[self.field].format(value.replace(' ', '-').lower())
            if url == "":
                url = result['url']

        keys = []

        template_name = 'app/seeker/column.html'
        if type(value) == AttrList:
            template_name = 'app/seeker/columnlist.html'
        elif type(value) == AttrDict:
            template_name = 'app/seeker/columndict.html'
            keys = list(value)
            value2 = {}
            for key in keys:
                newval = value[key]
                if type(newval) == int:
                    newval = "{0:d}".format(newval)
                elif type(newval) == float:
                    newval = "{0:.2f}".format(newval)
                value2[key] = newval
            value = value2
            print("Column.render: AttrDict found {0} with value {1}".format(self.field, value))
        elif type(value) == str:
            if value[:4] == 'http':
                template_name = 'app/seeker/columnimg.html'

        params = {
            'result': result,
            'field': self.field,
            'keys' : keys,
            'value': value,
            'highlight': highlight,
            'url': url,
            'view': self.view,
            #'user': self.view.request.user,
            'query': self.view.get_keywords_q(),
        }
        params.update(self.context(result, **kwargs))
        return loader.render_to_string(template_name, params)
        #return self.template.render(Context(params))

    def sortcolumn(self, sortarg):
        if self.sort == None:
            return None
        if sortarg.startswith('-'):
            sortdsl = '-%s' % self.sort
        else:
            sortdsl = self.sort
        return(sortdsl)


    def export_value(self, result):
        export_field = self.field if self.export is True else self.export
        if export_field:
            value = getattr(result, export_field, '')
            export_val = ', '.join(force_text(v.to_dict() if hasattr(v, 'to_dict') else v) for v in value) if isinstance(value, AttrList) else seeker_format(value)
        else:
            export_val = ''
        return export_val


class NestedColumn (Column):
    nestedfacet = None

    def __init__(self, field, label=None, sort=None, value_format=None, template=None, header=None, export=True, highlight=None, nestedfacet=None):
        self.nestedfacet = nestedfacet
        # overwrite get_field_sort()
        sort = {nestedfacet.nestedfield+".prc" : {"order" : "desc", "mode" : "max"}}
        super(NestedColumn, self).__init__(field, label, sort, value_format, template, header, export, highlight)

    def render(self, result, facets, **kwargs):
        value = getattr(result, self.field, None)
        if self.value_format:
            value = self.value_format(value)
        try:
            if '*' in self.highlight:
                # If highlighting was requested for multiple fields, grab any matching fields as a dictionary.
                r = self.highlight.replace('*', r'\w+').replace('.', r'\.')
                highlight = {f: result.meta.highlight[f] for f in result.meta.highlight if re.match(r, f)}
            else:
                highlight = result.meta.highlight[self.highlight]
        except:
            highlight = []
        if self.field in self.view.sumheader:
            url = result.url
        else:
            url = ""

        value2 = AttrList([])
        selval = facets[self.nestedfacet]
        if value:
            for v in value:
                # NestedFacet
                if 'val' in v:
                    newval = v['val']+": {0:4.2f}".format(v['prc'])
                    if len(selval) > 0:
                        if v['val'] in selval:
                            value2.append(newval)
                # OptionFacet
                if 'question' in v:
                    answer_value = v['answer']
                    if type(answer_value) == int or type(answer_value) == float:
                        answer_value = int(float(answer_value))
                    option_value = v['question']+'^'+answer_value
                    if len(selval) > 0:
                        if option_value in selval:
                            value2.append(v['question']+': '+answer_value)
                #else:
                #    value2.append(newval)
        value = value2

        params = {
            'result': result,
            'field': self.field,
            'value': value,
            'highlight': highlight,
            'url': url,
            'view': self.view,
            'user': self.view.request.user,
            'query': self.view.get_keywords_q(),
        }

        params.update(self.context(result, **kwargs))
        template_name = 'app/seeker/columnlist.html'

        return loader.render_to_string(template_name, params)

    def sortcolumn(self, sortarg):
        if self.sort == None:
            return None
        field_prc = self.nestedfacet.nestedfield+".prc"
        sortdsl = {field_prc : {"nested_path": self.nestedfacet.nestedfield, "mode": "max"}}
        nested_filter = self.nestedfacet.sort()
        if nested_filter:
            sortdsl[field_prc]["nested_filter"] = nested_filter
        if sortarg.startswith('-'):
            sortdsl[field_prc]["order"] = "desc"
        else:
            sortdsl[field_prc]["order"] = "asc"
        return(sortdsl)


class SeekerView (View):
    document = None
    """
    A :class:`elasticsearch_dsl.DocType` class to present a view for.
    """

    using = None
    """
    The ES connection alias to use.
    """

    index = None
    """
    The ES index to use. Defaults to the SEEKER_INDEX setting.
    """

    template_name = 'app/seeker/seeker.html'
    """
    The overall seeker template to render.
    """

    header_template = 'app/seeker/header.html'
    """
    The template used to render the search results header.
    """

    results_template = 'app/seeker/results.html'
    """
    The template used to render the search results.
    """

    footer_template = 'app/seeker/footer.html'
    """
    The template used to render the search results footer.
    """

    columns = None
    """
    A list of Column objects, or strings representing mapping field names. If None, all mapping fields will be available.
    """

    exclude = None
    """
    A list of field names to exclude when generating columns.
    """

    display = None
    """
    A list of field/column names to display by default.

    """
    summary = None
    sumheader = None
    urlfields = {}
    """
    A list of field/column names to use for summary.
    """

    required_display = []
    """
    A list of tuples, ex. ('field name', 0), representing field/column names that will always be displayed (cannot be hidden by the user).
    The second value is the index/position of the field (used as the index in list.insert(index, 'field name')).
    """

    @property
    def required_display_fields(self):
        return [t[0] for t in self.required_display]

    sort = None
    """
    A list of field/column names to sort by default, or None for no default sort order.
    """

    search = None
    """
    A list of field names to search. By default, will included all fields defined on the document mapping.
    """

    highlight = True
    """
    A list of field names to highlight, or True/False to enable/disable highlighting for all fields.
    """

    highlight_encoder = 'html'
    """
    An 'encoder' parameter is used when highlighting to define how highlighted text will be encoded. It can be either
    'default' (no encoding) or 'html' (will escape html, if you use html highlighting tags).
    """

    facets = []
    facets_keyword = None
    """
    A list of :class:`seeker.Facet` objects that are available to facet the results by.
    """

    initial_facets = {}
    """
    A dictionary of initial facets, mapping fields to lists of initial values.
    """

    page_size = 10
    """
    The number of results to show per page.
    """

    page_spread = 7
    """
    The number of pages (not including first and last) to show in the paginator widget.
    """

    can_save = True
    """
    Whether searches for this view can be saved.
    """

    export_name = 'seeker'
    """
    The filename (without extension, which will be .csv) to use when exporting data from this view.
    """

    export_timestamp = False
    """
    Whether or not to append a timestamp of the current time to the export filename when exporting data from this view.
    """

    show_rank = True
    """
    Whether or not to show a Rank column when performing keyword searches.
    """

    field_columns = {}
    """
    A dictionary of field column overrides.
    """

    field_labels = {}
    """
    A dictionary of field label overrides.
    """

    sort_fields = {}
    """
    A dictionary of sort field overrides.
    """

    highlight_fields = {}
    """
    A dictionary of highlight field overrides.
    """

    query_type = getattr(settings, 'SEEKER_QUERY_TYPE', 'query_string')
    """
    The query type to use when performing keyword queries (either 'query_string' (default) or 'simple_query_string').
    """

    operator = getattr(settings, 'SEEKER_DEFAULT_OPERATOR', 'AND')
    """
    The query operator to use by default.
    """

    permission = None
    """
    If specified, a permission to check (using ``request.user.has_perm``) for this view.
    """

    extra_context = {}
    """
    Extra context variables to use when rendering. May be passed via as_view(), or overridden as a property.
    """

    summary_list = [{'header': "Header", 'sentences': [("Excutere Auto Summary to get a summary list of your query selection", "Auto", 1)], 'url': ''}]
    NGRAM_SIZE = 2
    SUMMARY_SIZE = 3
    SUMMARY_URL = ''
    """
    The summary as obtained from the last Summary run. A summary contains a list of sentences with for each sentence a Ngram count
    """

    # The workbook describes how the result of the query should be reported: which columns, facets, graphs, charts and storyboards.
    # This selection is based on the facets selection.
    #
    # A storyboard holds: 1) a sequence number, 2) a dashboard layout 3) dashboard definitions 4) selection values
    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': ''}
    decoder = None
    dashboard = {}
    dashboard_layout = {}
    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ]
    tiles = []
    qst2fld = {}

    #workbook = {
    #    }

    # keep track of the ES aggregations for facets, charts and tiles. For each facet that is added to a chart or tile, its apply method
    # should simply add a (sub-)aggregation to the stack of bucket aggregates.
    aggs_stack = {}

    def normalized_querystring(self, qs=None, ignore=None):
        """
        Returns a querystring with empty keys removed, keys in sorted order, and values (for keys whose order does not
        matter) in sorted order. Suitable for saving and comparing searches.

        :param qs: (Optional) querystring to use; defaults to request.GET
        :param ignore: (Optional) list of keys to ignore when building the querystring
        """
        data = QueryDict(qs) if qs is not None else self.request.GET
        parts = []
        for key in sorted(data):
            if ignore and key in ignore:
                continue
            if not data[key]:
                continue
            if key == 'p' and data[key] == '1':
                continue
            values = data.getlist(key)
            # Make sure display/facet/sort fields maintain their order. Everything else can be sorted alphabetically for consistency.
            if key not in ('d', 'f', 's'):
                values = sorted(values)
#           parts.extend(urllib.urlencode({key: val}) for val in values)
            parts.extend(urllib.parse.urlencode({key: val}) for val in values)
        return '&'.join(parts)

    def get_field_label(self, field_name):
        """
        Given a field name, returns a human readable label for the field.
        """
        if field_name.endswith('.raw'):
            field_name = field_name[:-4]
        if field_name in self.field_labels:
            return self.field_labels[field_name]
        try:
            # If the document is a ModelIndex, try to get the verbose_name of the Django field.
            f = self.document.queryset().model._meta.get_field(field_name)
            return f.verbose_name.capitalize()
        except:
            # Otherwise, just make the field name more human-readable.
            return field_name.replace('_', ' ').capitalize()

    def get_field_sort(self, field_name):
        """
        Given a field name, returns the field name that should be used for sorting. If a mapping defines
        a .raw sub-field, that is used, otherwise the field name itself is used if index=not_analyzed.
        """
        if field_name.endswith('.raw'):
            return field_name
        if field_name in self.sort_fields:
            return self.sort_fields[field_name]
        if field_name in self.document._doc_type.mapping:
            dsl_field = self.document._doc_type.mapping[field_name]
            if isinstance(dsl_field, (dsl.Object, dsl.Nested)):
                return None
#            if not isinstance(dsl_field, dsl.String):
            if not isinstance(dsl_field, dsl.Text):
                return field_name
            if 'raw' in dsl_field.fields:
                return '%s.raw' % field_name
            elif getattr(dsl_field, 'index', None) == 'not_analyzed':
                return field_name
        return None

    def get_field_highlight(self, field_name):
        if field_name in self.highlight_fields:
            return self.highlight_fields[field_name]
        if field_name in self.document._doc_type.mapping:
            dsl_field = self.document._doc_type.mapping[field_name]
            if isinstance(dsl_field, (dsl.Object, dsl.Nested)):
                return '%s.*' % field_name
            return field_name
        return None

    def get_field_value_format(self, field_name):
        if field_name in self.document._doc_type.mapping:
            dsl_field = self.document._doc_type.mapping[field_name]
            if dsl_field.name == 'date':
                return date_value_format
        return None

    def make_column(self, field_name):
        """
        Creates a :class:`seeker.Column` instance for the given field name.
        """
        if field_name in self.field_columns:
            return self.field_columns[field_name]
        label = self.get_field_label(field_name)
        sort = self.get_field_sort(field_name)
        highlight = self.get_field_highlight(field_name)
        value_format = self.get_field_value_format(field_name)
        for facet in self.facets:
            if type(facet) == seeker.NestedFacet:
                if facet.nestedfield == field_name:
                    return NestedColumn(field_name, label=label, sort=sort, highlight=highlight, value_format=value_format, nestedfacet=facet)
            if type(facet) == seeker.OptionFacet:
                if facet.nestedfield == field_name:
                    return NestedColumn(field_name, label=label, sort=sort, highlight=highlight, value_format=value_format, nestedfacet=facet)
        return Column(field_name, label=label, sort=sort, highlight=highlight, value_format=value_format)

    def get_columns(self):
        """
        Returns a list of :class:`seeker.Column` objects based on self.columns, converting any strings.
        """
        columns = []
        if not self.columns:
            # If not specified, all mapping fields will be available.
            for f in self.document._doc_type.mapping:
                if self.exclude and f in self.exclude:
                    continue
                columns.append(self.make_column(f))
        else:
            # Otherwise, go through and convert any strings to Columns.
            for c in self.columns:
                if isinstance(c, six.string_types):
                    if self.exclude and c in self.exclude:
                        continue
                    columns.append(self.make_column(c))
                elif isinstance(c, Column):
                    if self.exclude and c.field in self.exclude:
                        continue
                    columns.append(c)
        # Make sure the columns are bound and ordered based on the display fields (selected or default).
        display = self.get_display()

        for c in columns:
            c.bind(self, c.field in display, c.field in self.summary, c.field in self.sumheader)
#        columns.sort(key=lambda c: display.index(c.field) if c.visible else c.label)
        columns.sort(key=lambda c: str(display.index(c.field)) if c.visible else c.label)
        return columns


    def get_keywords_q(self):
        return self.request.GET.get('q', '').strip()

    def get_keywords_k(self):
        keywords_k = self.request.GET.get('keywords_k', '').strip()
        if keywords_k == '':
            keywords_k = []
        else:
            keywords_k = keywords_k.split(',')
        return keywords_k

    def get_display(self):
        """
        Returns a list of display field names. If the user has selected display fields, those are used, otherwise
        the default list is returned. If no default list is specified, all fields are displayed.
        """
        default = list(self.display) if self.display else list(self.document._doc_type.mapping)
        display_fields = self.request.GET.getlist('d') or default
        display_fields = [f for f in display_fields if f not in self.required_display_fields]
        for field, i in self.required_display:
            display_fields.insert(i, field)
        return display_fields

    def get_saved_search(self):
        """
        Returns the "saved_search" GET parameter if it's in the proper format, otherwise returns None.
        """
        saved_search_vals = [val for val in self.request.GET.getlist('saved_search') if val]
        if len(saved_search_vals) == 1 and saved_search_vals[0].isdigit():
            return saved_search_vals[0]
        return None

    def get_facets(self):
        facet_l = []
        for facet in self.facets:
            facet.visible_pos = int(float(self.request.GET.get('a'+facet.field, "{0:d}".format(facet.visible_pos))))
            facet_l.append(facet)
        facet_l.sort(key=lambda f: f.visible_pos)
        return facet_l

    def get_facets_keyword(self):
        facet_l = []
        for facet in self.facets_keyword:
            facet.set_search_fields(self.get_search_fields())
            facet_l.append(facet)
        return facet_l

    def get_facet_selected_data(self, initial=None, exclude=None):
        if initial is None:
            initial = {}
        facets = collections.OrderedDict()
        for f in self.get_facets():
            if f.field != exclude:
                facets[f] = self.request.GET.getlist(f.field) or initial.get(f.field, [])
                if facets[f] == [''] or facets[f] == ['All']:  
                    facets[f] = []
        return facets

    def get_facets_data(self, results, tiles_select, benchmark):
        facets_data = OrderedDict()
        for f in self.get_facets():
            if type(f) == seeker.facets.TermsFacet and f.visible_pos > 0 and f.field in results.aggregations and f.field in self.tiles:
                if f.label in tiles_select:
                    selected = True
                else:
                    selected = False
                keys = [key for key in f.buckets(results.aggregations[f.field])]
                facets_data[f.field] = {'label': f.label, 'selected': selected, 'benchmark': benchmark, 'values': keys}
        return facets_data

    def get_facet_tile(self):
        facets = collections.OrderedDict()
        for f in self.get_facets():
            tile_checkbox = self.request.GET.get(f.field+'_tile')
            if tile_checkbox == 'on':
                facets[f] = self.request.GET.get(f.field+'_tile')
        tile_facet_field = self.request.GET.get('tile_facet_field', '')
        f = self.get_facet_by_field_name(tile_facet_field)
        if f:
            facets[f] = 'on'
        return facets

    def get_benchmark(self):
        # return a list of benchmarks, so far only one can be specified.
        benchmark = self.request.GET.get('benchmark')
        if benchmark == '' or benchmark == 'All':
            benchmark = []
        else:
            benchmark = [benchmark]
        return benchmark

    def get_facets_keyword_selected_data(self, exclude=None):
        facets_keyword = collections.OrderedDict()
        for f in self.get_facets_keyword():
            if f.field != exclude:
                keywords_input = self.request.GET.get(f.keywords_input, '')
                # incase a file is read, the input field holds the filename. Make it empty and
                # force the read_keywords into the input field.
                if 'keyword_button' in self.request.GET:
                    if f.name + '_read' == self.request.GET['keyword_button']:
                        keywords_input = f.read_keywords
                f.keywords_text = keywords_input.strip()
                if f.keywords_text == '' and f.initial:
                    f.keywords_text = f.initial
                if f.keywords_text == '':
                    f.keywords_k = []
                else:
                    f.keywords_k = f.keywords_text.split(',')
                facets_keyword[f] = self.request.GET.getlist(f.field)
        return facets_keyword

    def get_facet_by_field_name(self, field_name):
        # check on the base name and not at possible extensions like .keyword
        base_field_name = field_name.split('.')[0]
        if base_field_name != 'answer' and base_field_name != '':
            for facet in self.facets:
                facet_base_field_name = facet.field.split('.')[0]
                if facet_base_field_name == base_field_name:
                    return facet
            for facet in self.facets_keyword:
                facet_base_field_name = facet.field.split('.')[0]
                if facet_base_field_name == base_field_name:
                    return facet
            print("get_facet_by_field_name: facet not found, field_name ", field_name)
            for qst, mapping in self.qst2fld.items():
                fields = mapping[0]
                field_type = mapping[1]
                if field_name in fields:
                    if field_type == 'nested_qst_ans':
                        facet = seeker.facets.OptionFacet(field_name, label = field_name, nestedfield=field_name, visible_pos=0)
                        return facet
            print("get_facet_by_field_name: facet also not found in qstfld, field_name ", field_name)
        return None

    def get_search_fields(self, mapping=None, prefix=''):
        if self.search:
            return self.search
        elif mapping is not None:
            fields = []
            for field_name in mapping:
                if mapping[field_name].to_dict().get('analyzer') == DEFAULT_ANALYZER:
                    fields.append(prefix + field_name)
                if hasattr(mapping[field_name], 'properties'):
                    fields.extend(self.get_search_fields(mapping=mapping[field_name].properties, prefix=prefix + field_name + '.'))
            return fields
        else:
            return self.get_search_fields(mapping=self.document._doc_type.mapping)

    def get_search_query_type(self, search, keywords_q, analyzer=DEFAULT_ANALYZER):
        kwargs = {'query': keywords_q,
                  'analyzer': analyzer,
                  'fields': self.get_search_fields(),
                  'default_operator': self.operator}
        if self.query_type == 'simple_query':
            kwargs['auto_generate_phrase_queries'] = True
        return search.query(self.query_type, **kwargs)

    def get_empty_search(self):
        using = self.using or self.document._doc_type.using or 'default'
        index = self.index or self.document._doc_type.index or getattr(settings, 'SEEKER_INDEX', 'seeker')
        # TODO: self.document.search(using=using, index=index) once new version is released
        s = self.document.search().index(index).using(using).extra(track_scores=True)
        return s


    def get_search(self, keywords_q=None, facets=None, facets_keyword=None, dashboard=None, aggregate=False):
        s = self.get_empty_search()

        if facets:
            for facet, values in facets.items():
                s = facet.filter(s, values)
                if aggregate or seeker.dashboard.facet_aggregate(facet, self.dashboard):
                    subaggr = False
                    body_kf = {}
                    if facets_keyword:
                        for facet_keyword in facets_keyword.keys():
                            if facet_keyword.keywords_k and dashboard:
                                for chart_name, chart in dashboard.items():
                                    if chart['data_type'] != "facet":
                                        continue
                                    if 'Y_facet' in chart:
                                        if chart['X_facet']['field'] == facet.field and chart['Y_facet']['field'] == facet_keyword.field:
                                            subaggr = True
                                            for kf in facet_keyword.keywords_k:
                                                body_kf[kf] = {'multi_match' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields()}}
                                            extra = {facet_keyword.field : {'filters': {'filters': body_kf }}}
                                            #facet.apply(s, facet.name, self.aggs_stack, aggs=extra), replaced by two aggs
                                            facet.apply(s, facet.name, self.aggs_stack)
                                            facet_keyword.apply(s, facet.name, self.aggs_stack, filters=body_kf)
                    if dashboard:
                        for facet2 in facets.keys():
                            for chart_name, chart in dashboard.items():
                                if chart['data_type'] != "facet":
                                    continue
                                if 'Y_facet' in chart:
                                    if chart['X_facet']['field'] == facet.field and chart['Y_facet']['field'] == facet2.field:
                                        subaggr = True
                                        extra = {}
                                        extra = {facet2.name : {'terms': {'field': facet2.field, 'size':40, 'min_doc_count':1}}}
                                        #facet.apply(s, facet.name, self.aggs_stack, aggs=extra)
                                        facet.apply(s, facet.name, self.aggs_stack)
                                        facet2.apply(s, facet.name, self.aggs_stack)
                    if not subaggr:
                        facet.apply(s, facet.name, self.aggs_stack)


        if facets_keyword:
            keywords_selected = ''
            for facet_keyword, values_keywords_k in facets_keyword.items():
                # incase the selected keywords have to be copied into the Search field
                keyword_search = False
                if 'keyword_button' in self.request.GET:
                    if facet_keyword.name + '_search' == self.request.GET['keyword_button']:
                        keyword_search = True
                if keyword_search:
                    for value_keyword in values_keywords_k:
                        if keywords_selected == '':
                            keywords_selected = value_keyword
                        else:
                            keywords_selected = keywords_selected + " OR " + value_keyword
                    facets_keyword[facet_keyword] = []
                else:
                    for value_keywords_k in values_keywords_k:
                        s = self.get_search_query_type(s, value_keywords_k)
                if facet_keyword.keywords_k:
                    body_kf = {}
                    for kf in facet_keyword.keywords_k:
                        #body_kf[kf] = {'multi_match' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields()}}
                        body_kf[kf] = {'simple_query_string' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields(), 'default_operator': self.operator}}
                    subaggr = False
                    term_kf = {}
                    subbody_kf = {}
                    if facet_keyword.keywords_k and dashboard:
                        for facet in facets.keys():
                            for chart_name, chart in dashboard.items():
                                if chart['data_type'] != "facet":
                                    continue
                                if 'Y_facet' in chart:
                                    if chart['X_facet']['field'] == facet_keyword.field and chart['Y_facet']['field'] == facet.field:
                                        subaggr = True
                                        #term_kf[facet.field] = {'terms' : {'field': facet.field}}
                                        #term_kf[facet.name] = facet.aggr()
                                        #s.aggs[facet_keyword.field] = {'filters': {'filters': body_kf }, 'aggs': term_kf}
                                        facet_keyword.apply(s, facet_keyword.name, self.aggs_stack, filters=body_kf)
                                        facet.apply(s, facet_keyword.name, self.aggs_stack)
                    if not subaggr:
                        #s.aggs[facet_keyword.field] = {'filters': {'filters': body_kf }}
                        facet_keyword.apply(s, facet_keyword.name, self.aggs_stack, filters=body_kf)
            if keywords_selected != '':
                keywords_q = keywords_selected

        if keywords_q:
            s = self.get_search_query_type(s, keywords_q)

        return s, keywords_q

    def get_aggr(self, s, dashboard=None):
        for chart_name, chart in dashboard.items():
            if chart['data_type'] != "aggr":
                continue
            X_facet = chart['X_facet']
            xfacet = self.get_facet_by_field_name(X_facet['field'])
            if 'Y_facet' not in chart:
                yfacet = None
            else:
                Y_facet = chart['Y_facet']
                yfacet = self.get_facet_by_field_name(Y_facet['field'])
            if 'order' in X_facet:
                #xfacet.apply(s, chart_name, self.aggs_stack, order=X_facet['order'])
                xfacet.aggr(s, chart_name, self.aggs_stack, order=X_facet['order'])
            else:
                #xfacet.apply(s, chart_name, self.aggs_stack)
                xfacet.aggr(s, chart_name, self.aggs_stack)
            if yfacet is not None:
                if 'order' in Y_facet:
                    #yfacet.apply(s, chart_name, self.aggs_stack, order=Y_facet['order'])
                    yfacet.aggr(s, chart_name, self.aggs_stack, order=Y_facet['order'])
                else:
                    #yfacet.apply(s, chart_name, self.aggs_stack)
                    yfacet.aggr(s, chart_name, self.aggs_stack)
        return s

    def get_tile_search(self, s, facet_tile, keywords_q=None, facets=None, facets_keyword=None, dashboard=None):
        #s = s.params(search_type="count")
        #The next charts can occur:
        # - 1) facet*facet, 2) facet*facet_keyword, 3) facet
        # - 4) facet_keyword*facet_keyword (NOT SUPPORTED), 5) facet_keyword*facet, 6) facet_keyword
        # All deep level aggregation replaced by data_type == aggr. Only 3 and 6 remain for facet and facet_keyword
        if keywords_q:
            s = self.get_search_query_type(s, keywords_q)
        if facets:
            for facet, values in facets.items():
                s = facet.filter(s, values)
                if seeker.dashboard.facet_aggregate(facet, dashboard):
                    subaggr = False
                    body_kf = {}
                    if facets_keyword:
                        for facet_keyword in facets_keyword.keys():
                            #if facet_keyword.keywords_k and dashboard:
                            if dashboard:
                                for chart_name, chart in dashboard.items():
                                    if chart['data_type'] != "facet":
                                        continue
                                    if 'Y_facet' in chart:
                                        if chart['X_facet']['field'] == facet.field and chart['Y_facet']['field'] == facet_keyword.field:
                                            subaggr = True
                                            for kf in facet_keyword.keywords_k:
                                                #body_kf[kf] = {'multi_match' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields()}}
                                                body_kf[kf] = {'simple_query_string' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields(),
                                                                                        'default_operator': self.operator}}
                                            extra = {
                                                facet.name : {'terms': {'field': facet.field},
                                                    facet_keyword.field : {'filters': {'filters': body_kf }}}
                                                }
                                            #facet_tile.apply_tile(s, chart_name, facet.field, facet_keyword.field, aggs=extra)
                                            # chart 2) facet * facet_keyword
                                            agg_name = facet_tile.name+'_'+chart_name
                                            facet_tile.apply(s, agg_name, self.aggs_stack)
                                            facet.apply(s, agg_name, self.aggs_stack)
                                            if len(body_kf) > 0:
                                                facet_keyword.apply(s, agg_name, self.aggs_stack, filters=body_kf)
                    for facet2 in facets.keys():
                        for chart_name, chart in dashboard.items():
                            if chart['data_type'] != "facet":
                                continue
                            if 'Y_facet' in chart:
                                if chart['X_facet']['field'] == facet.field and chart['Y_facet']['field'] == facet2.field:
                                    subaggr = True
                                    extra = {
                                        facet.name : {'terms': {'field': facet.field},
                                            facet2.name : {'terms': {'field': facet2.field }}}
                                        }
                                    #facet_tile.apply_tile(s, chart_name, facet.field, facet2.field, aggs=extra)
                                    # chart 1) facet * facet
                                    agg_name = facet_tile.name+'_'+chart_name
                                    facet_tile.apply(s, agg_name, self.aggs_stack)
                                    facet.apply(s, agg_name, self.aggs_stack)
                                    facet2.apply(s, agg_name, self.aggs_stack)
                    for chart_name, chart in dashboard.items():
                        if chart['data_type'] != "facet":
                            continue
                        single = False
                        nested = False
                        # chart 3) facet
                        agg_name = facet_tile.name+'_'+chart_name
                        if 'Y_facet' not in chart:
                            single = True
                        elif chart['Y_facet']['field'] == "answer":
                            nested = True
                        if chart['X_facet']['field'] == facet.field and (single or nested):
                            if single:
                                #extra = {facet.name : facet.aggr(agg_name, self.aggs_stack)}
                                #facet_tile.apply_tile(s, chart_name, facet.field, None, aggs=extra)
                                facet_tile.apply(s, agg_name, self.aggs_stack)
                                facet.apply(s, agg_name, self.aggs_stack)
                            elif nested:
                                #facet_tile.apply_tile_nested(s, agg_name, facet.nestedfield)
                                facet_tile.apply(s, agg_name, self.aggs_stack)
                                facet.apply(s, agg_name, self.aggs_stack)

        if facets_keyword:
            for facet_keyword, values_keywords_k in facets_keyword.items():
                for value_keywords_k in values_keywords_k:
                    s = self.get_search_query_type(s, value_keywords_k)
                if facet_keyword.keywords_k:
                    body_kf = {}
                    for kf in facet_keyword.keywords_k:
                        #body_kf[kf] = {'multi_match' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields()}}
                        body_kf[kf] = {'simple_query_string' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.get_search_fields(),
                                                                'default_operator': self.operator}}
                    subaggr = False
                    term_kf = {}
                    subbody_kf = {}
                    #if facet_keyword.keywords_k and dashboard:
                    if dashboard:
                        for facet in facets.keys():
                            for chart_name, chart in dashboard.items():
                                if chart['data_type'] != "facet":
                                    continue
                                agg_name = facet_tile.name+'_'+chart_name
                                if 'Y_facet' in chart:
                                    if chart['X_facet']['field'] == facet_keyword.field and chart['Y_facet']['field'] == facet.field:
                                        subaggr = True
                                        #term_kf[facet.field] = {'terms' : {'field': facet.field}}
                                        #term_kf[facet.name] = facet.aggr()
                                        # chart 5) facet_keyword * facet
                                        facet_tile.apply(s, agg_name, self.aggs_stack)
                                        if len(body_kf) > 0:
                                            facet_keyword.apply(s, agg_name, self.aggs_stack, filters=body_kf)
                                        facet.apply(s, agg_name, self.aggs_stack)
                        if not subaggr:
                            for chart_name, chart in dashboard.items():
                                if chart['data_type'] != "facet":
                                    continue
                                agg_name = facet_tile.name+'_'+chart_name
                                if 'Y_facet' not in chart:
                                    if chart['X_facet']['field'] == facet_keyword.field:
                                        #s.aggs[facet_keyword.field] = {'filters': {'filters': body_kf }}
                                        # chart 6) facet_keyword
                                        facet_tile.apply(s, agg_name, self.aggs_stack)
                                        facet_keyword.apply(s, agg_name, self.aggs_stack, filters=body_kf)

        return s

    def get_tile_aggr(self, s, facet_tile, dashboard=None):
        for chart_name, chart in dashboard.items():
            if chart['data_type'] != "aggr":
                continue
            X_facet = chart['X_facet']
            xfacet = self.get_facet_by_field_name(X_facet['field'])
            if 'Y_facet' not in chart:
                yfacet = None
            else:
                Y_facet = chart['Y_facet']
                yfacet = self.get_facet_by_field_name(Y_facet['field'])
            agg_name = facet_tile.name+'_'+chart_name
            if yfacet == None:
                facet_tile.aggr(s, agg_name, self.aggs_stack)
                xfacet.aggr(s, agg_name, self.aggs_stack)
            else:
                facet_tile.aggr(s, agg_name, self.aggs_stack)
                xfacet.aggr(s, agg_name, self.aggs_stack)
                yfacet.aggr(s, agg_name, self.aggs_stack)
        return s

    # the storyboard (self.storyboard) and charts (self.dashboard) of the specified workbook_name are set
    # in case also a dashboard_name is specified and that workbook runs in pull mode, only the charts and base-charts
    # of that dashboard are set (self.dashboard).
    # The workbook and dashboard objects of the specified workbook_name and dashboard_name are returned.
    def get_workbook_dashboard_names(self):
        workbook = {}
        dashboard = None
        workbook_name = self.request.GET.get('workbook_name', '').strip()
        storyboard_name = self.request.GET.get('storyboard_name', '').strip()
        if workbook_name == '':
            workbook_name = 'initial'
        dashboard_data = 'push'
        if hasattr(self, 'workbooks'):
            if workbook_name in self.workbooks:
                workbook = self.workbooks[workbook_name]
                if 'facets' in workbook:
                    for facet in self.facets:
                        if facet.field in workbook['facets']:
                            facet.visible_pos = 1
                        else:
                            facet.visible_pos = 0
                # don't overwrite the default on seekerview level (excel views)
                if 'display' in workbook:
                    self.display = workbook['display']
                self.dashboard = workbook.get('charts', [])
                self.tiles = workbook.get('tiles', [])
                if 'storyboards' in workbook:
                    storyboards = workbook['storyboards']
                    if storyboard_name in storyboards:
                        self.storyboard = storyboards[storyboard_name]
                    else:
                        self.storyboard = storyboards['initial']
                dashboard_data = workbook.get('dashboard_data', 'push')
                self.qst2fld = workbook.get('qst2fld', {})
        dashboard_name = self.request.GET.get('dashboard_name', '').strip()
        if dashboard_name == '':
            dashboard_name = self.storyboard[0]['name']
        for db in self.storyboard:
            if db['name'] == dashboard_name:
                dashboard = db
                db['dashboard_data'] = 'push'
            else:
                db['dashboard_data'] = dashboard_data
        if workbook_name != '' and dashboard_name != '' and dashboard_data == 'pull':
            self.dashboard = {};
            for layout_name, layout in dashboard['layout'].items():
                for row in layout:
                    for chart_name in row:
                        chart = workbook['charts'][chart_name]
                        self.dashboard[chart_name] = chart
                        if 'base' in chart:
                            if type(chart['base']) == list:
                                for base_chart_name in chart['base']:
                                    self.dashboard[base_chart_name] = workbook['charts'][base_chart_name]
                            else:
                                base_chart_name = chart['base']
                                self.dashboard[base_chart_name] = workbook['charts'][base_chart_name]
        #seeker.dashboard.charts_template(self, dashboard)
        return workbook, dashboard

    def set_workbook_filters(self, facets, workbook):
        if 'filters'in workbook:
            filters = workbook['filters']
            for field, values in filters.items():
                for facet in facets:
                    if facet.field == field:
                        facets[facet].extend(values)


    def render(self):
        #from app.models import SavedSearch

        querystring = self.normalized_querystring(ignore=['p', 'saved_search'])

        #if self.request.user and self.request.user.is_authenticated() and not querystring and not self.request.is_ajax():
        #    default = self.request.user.seeker_searches.filter(url=self.request.path, default=True).first()
        #    if default and default.querystring:
        #        return redirect(default)

        ## Figure out if this is a saved search, and grab the current user's saved searches.
        saved_search = None
        saved_searches = []
        self.aggs_stack = None
        self.aggs_stack = {}
        #if self.request.user and self.request.user.is_authenticated():
        #    saved_search_pk = self.get_saved_search()
        #    if saved_search_pk:
        #        try:
        #            saved_search = self.request.user.seeker_searches.get(pk=saved_search_pk, url=self.request.path, querystring=querystring)
        #        except SavedSearch.DoesNotExist:
        #            pass
        #    saved_searches = list(self.request.user.seeker_searches.filter(url=self.request.path))
        #else:
        #    saved_searches = []

        workbook, dashboard = self.get_workbook_dashboard_names()
        keywords_q = self.get_keywords_q()
        facets = self.get_facet_selected_data(initial=self.initial_facets if not self.request.is_ajax() else None)
        facets_keyword = self.get_facets_keyword_selected_data()
        self.set_workbook_filters(facets, workbook)

        search, keywords_q = self.get_search(keywords_q, facets, facets_keyword, self.dashboard)
        search = self.get_aggr(search, self.dashboard)
        columns = self.get_columns()

        # Make sure we sanitize the sort fields.
        sort_fields = []
        column_lookup = {c.field: c for c in columns}
        if saved_search:
            sorts = self.request.GET.getlist('s')
        else:
            sorts = self.request.GET.getlist('s') or self.sort or []
        for s in sorts:
            # Get the column based on the field name, and use it's "sort" field, if applicable.
            c = column_lookup.get(s.lstrip('-'))
            if c:
                sort = c.sortcolumn(s)
                if sort:
                    sort_fields.append(sort)

        # Highlight fields.
        if self.highlight:
            highlight_fields = self.highlight if isinstance(self.highlight, (list, tuple)) else [c.highlight for c in columns if c.visible and c.highlight]
            search = search.highlight(*highlight_fields, number_of_fragments=0).highlight_options(encoder=self.highlight_encoder)

        # Calculate paging information.
        page = self.request.GET.get('p', '').strip()
        page = int(page) if page.isdigit() else 1
        offset = (page - 1) * self.page_size
        results_count = search[0:0].execute().hits.total
        if results_count < offset:
            page = 1
            offset = 0

        # Finally, grab the results.
        results = search.sort(*sort_fields)[offset:offset + self.page_size].execute()

        #if self.summary != None:, also fill url in results
        self.summary_tab(results, columns)

        benchmark = self.get_benchmark()
        tiles_select = OrderedDict()
        tiles_d = {chart_name : {} for chart_name in self.dashboard.keys()}
        seeker.dashboard.bind_tile(self, tiles_select, tiles_d, None, results, benchmark)
        seeker.models.stats_df = pd.DataFrame()

        facets_tile = self.get_facet_tile()
        if len(facets_tile) > 0:
            search_tile = self.get_empty_search()
            for facet_tile in facets_tile:
                search_tile = self.get_tile_search(search_tile, facet_tile, keywords_q, facets, facets_keyword, self.dashboard)
                search_tile = self.get_tile_aggr(search_tile, facet_tile, self.dashboard)
            results_tile = search_tile.execute(ignore_cache=True)
            seeker.dashboard.bind_tile(self, tiles_select, tiles_d, facets_tile, results_tile, benchmark)

        seeker.models.stats_df = pd.DataFrame()
        for chart_name, chart in self.dashboard.items():
            data_type = chart['data_type']
            if data_type == 'correlation':
                seeker.models.stats_df = seeker.dashboard.stats(self, chart_name, tiles_d)
                chart_data, meta_data = seeker.dashboard.bind_correlation(self, chart, seeker.models.stats_df)
                tiles_d[chart_name]['All'] = {'chart_data' : chart_data, 'meta_data' : meta_data}
            if data_type == 'card_ttest':
                self.aggs_stack = None
                self.aggs_stack = {}
                search_hits, keywords_q = self.get_search(keywords_q, facets, facets_keyword, dashboard=None)
                results_hits = search_hits[0:10000].execute(ignore_cache=True)
                chart_data, meta_data = seeker.cards.ttest(self, chart_name, chart, results_hits.hits, results_hits.aggregations, 'All', benchmark)
                tiles_d[chart_name]['All'] = {'chart_data' : chart_data, 'meta_data' : meta_data}
            if data_type == 'join':
                tiles_d[chart_name]['All'] =  {'chart_data' : [], 'meta_data' : {}}

        context_querystring = self.normalized_querystring()
        sort = sorts[0] if sorts else ''
        facets_data = self.get_facets_data(results, tiles_select, benchmark)

        context = {
            'document': self.document,
            'keywords_q': keywords_q,
            'columns': columns,
            'optional_columns': [c for c in columns if c.field not in self.required_display_fields],
            'display_columns': [c for c in columns if c.visible],
            'summary_list': self.summary_list,
            'facets': facets,
            'facets_keyword': facets_keyword,
            'selected_facets': self.request.GET.getlist('f') or self.initial_facets.keys(),
            'form_action': self.request.path,
            'results': results,
            'facets_data': json.dumps(facets_data),
            'tiles_select': json.dumps(tiles_select),
            'tiles_d': json.dumps(tiles_d),
            #'stats_df' : seeker.models.stats_df.to_json(orient='records'),
            'storyboard' : json.dumps(self.storyboard),
            'dashboard_name' : dashboard['name'],
            'dashboard': json.dumps(self.dashboard),
            'tabs' : self.tabs,
            'page': page,
            'page_size': self.page_size,
            'page_spread': self.page_spread,
            'sort': sort,
            'querystring': context_querystring,
            'reset_querystring': self.normalized_querystring(ignore=['p', 's', 'saved_search']),
            'show_rank': self.show_rank,
            'export_name': self.export_name,
            #'can_save': self.can_save and self.request.user and self.request.user.is_authenticated(),
            'header_template': self.header_template,
            'results_template': self.results_template,
            'footer_template': self.footer_template,
            'saved_search': saved_search,
            'saved_searches': saved_searches,
        }

        if self.extra_context:
            context.update(self.extra_context)

        if self.request.is_ajax():
            view_name = self.request.GET.get('view_name', '')
            return JsonResponse({
                'view_name' : view_name,
                'querystring': context_querystring,
                'page': page,
                'sort': sort,
                'facets_data': json.dumps(facets_data),
                'storyboard' : json.dumps(self.storyboard),
                'dashboard_name' : dashboard['name'],
                'dashboard': json.dumps(self.dashboard),
                'tiles_select': json.dumps(tiles_select),
                'tiles_d': json.dumps(tiles_d),
                #'stats_df' : seeker.models.stats_df.to_json(orient='records'),
            })
        else:
            return render(self.request, self.template_name, context)

    def render_facet_query(self):
        keywords_q = self.get_keywords_q()
        facet = {f.field: f for f in self.get_facets()}.get(self.request.GET.get('_facet'))
        if not facet:
            raise Http404()
        # We want to apply all the other facet filters besides the one we're querying.
        facets = self.get_facet_selected_data(exclude=facet)
        search = self.get_search(keywords_q, facets, aggregate=False)
        fq = '.*' + self.request.GET.get('_query', '').strip() + '.*'
        facet.apply(search, facet.name, include={'pattern': fq, 'flags': 'CASE_INSENSITIVE'})
        return JsonResponse(facet.data(search.execute()))

    def export(self):
        """
        A helper method called when ``_export`` is present in ``request.GET``. Returns a ``StreamingHttpResponse``
        that yields CSV data for all matching results.
        """

        self.aggs_stack = None
        self.aggs_stack = {}
        self.get_workbook()

        keywords_q = self.get_keywords_q()
        facets = self.get_facet_selected_data()
        facets_keyword = self.get_facets_keyword_selected_data()

        search, keywords_q = self.get_search(keywords_q, facets, facets_keyword, self.dashboard)
        #search = self.get_search(keywords_q, facets, aggregate=False)
        columns = self.get_columns()

        def csv_escape(value):
            if isinstance(value, (list, tuple)):
                value = '; '.join(force_text(v) for v in value)
            return '"%s"' % force_text(value).replace('"', '""')

        def csv_generator():
            yield ','.join('"%s"' % c.label for c in columns if c.visible and c.export) + '\n'
            for result in search.scan():
                yield ','.join(csv_escape(c.export_value(result)) for c in columns if c.visible and c.export) + '\n'

        export_timestamp = ('_' + timezone.now().strftime('%m-%d-%Y_%H-%M-%S')) if self.export_timestamp else ''
        export_name = '%s%s.csv' % (self.export_name, export_timestamp)
        resp = StreamingHttpResponse(csv_generator(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename=%s' % export_name
        return resp

    def read_keywords(self, facet_keyword, keyword_filename):
        keywords_input = ''
        keyword_file = os.path.join(BASE_DIR, 'data/' + keyword_filename)
        try:
            file = open(keyword_file, 'r')
            pyfile = File(file)
            for line in pyfile:
                keyword = line.rstrip('\n')
                if keyword.count(' ') > 0 and keyword[0] != '"':
                    keyword = '"' + keyword + '"'
                if keywords_input == '':
                    keywords_input = keyword
                else:
                    keywords_input = keywords_input + ',' + keyword
            pyfile.close()
        except:
            cwd = os.getcwd()
            print("read_keywords: working dirtory is: ", cwd)
            print("read_keywords: keyword_file: ", keyword_file)
            return False
        facet_keyword.read_keywords = keywords_input
        return True


    def summary_tab(self, results, columns):
        """
        A helper method called when ``_summary`` is present in ``request.GET``.
        It will prepare a summary list of key sentences of the queried items on the selected summary fields
        """

        #keywords_q = self.get_keywords_q()
        #keywords_k = self.get_keywords_k()
        #facets = self.get_facet_selected_data()
        #facets_keyword = self.get_facets_keyword_selected_data()
        #search = self.get_search(keywords_q, facets, keywords_k, facets_keyword, aggregate=False)
        #columns = self.get_columns()
        #results = search.execute()

        summary_count = 0
        self.summary_list = None
        self.summary_list = []

        for result in results:
            header = ""
            id = getattr(result, '_id', '')
            url = self.SUMMARY_URL.format(id)
            if 'url' not in result:
                result['url'] = url
            for c in columns:
                if c.sumheader:
                    header_field = getattr(result, c.field, '')
                    if header_field:
                        header = header + header_field
            article = ""
            for c in columns:
                if c.summary:
                    article = article + getattr(result, c.field, '')
            ngrams = get_ngrams(article, self.NGRAM_SIZE)
            nr_smry_sent = min(self.SUMMARY_SIZE, len(ngrams))
            sentence_list = []
            sentences = re.split('\.|\n', article)
#           sentences = article.split('.')
            smry_sent_nr = 0
            for ngram in list(ngrams.items()):
                for sentence in sentences:
                    clean_sentence = " ".join(clean_input(sentence))
                    if ngram[0] in clean_sentence:
                        # sentence should be a real sentence and not a header that equals the ngram
                        if ngram[0] != clean_sentence:
                            # replace " by ', otherwise " wil cause prolbem in the Template
                            clean_sentence = clean_sentence.replace("\"", "\'")
                            sentence_list.append((clean_sentence, ngram[0], ngram[1]))
                            sentences.remove(sentence)
                            smry_sent_nr = smry_sent_nr + 1
                            break
                if smry_sent_nr >= nr_smry_sent:
                    break

            self.summary_list.append({'header': header, 'sentences': sentence_list, 'url': url})
            summary_count = summary_count + 1

    def get(self, request, *args, **kwargs):
        if '_facet' in request.GET:
            return self.render_facet_query()
        if '_export' in request.GET:
            return self.export()
        if 'keyword_button' in request.GET:
            for facet_keyword in self.facets_keyword:
                if facet_keyword.name + '_read' == request.GET['keyword_button']:
                    keyword_filename = request.GET[facet_keyword.keywords_input]
                    self.read_keywords(facet_keyword, keyword_filename)
        return self.render()

    def post(self, request, *args, **kwargs):
        if not self.can_save:
            return redirect(request.get_full_path())
        post_qs = request.POST.get('querystring', '')
        qs = self.normalized_querystring(post_qs, ignore=['p', 'saved_search'])
        saved_search_pk = request.POST.get('saved_search', '').strip()
        if not saved_search_pk.isdigit():
            saved_search_pk = None
        if '_save' in request.POST:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, 'You did not provide a name for this search. Please try again.')
                return redirect('%s?%s' % (request.path, post_qs))
            default = request.POST.get('default', '').strip() == '1'
            if default:
                request.user.seeker_searches.filter(url=request.path).update(default=False)
            search_values = {'querystring': qs, 'default': default}
            search, created = request.user.seeker_searches.update_or_create(name=name, url=request.path, defaults=search_values)
            messages.success(request, 'Successfully saved "%s".' % search)
            return redirect(search)
        elif '_default' in request.POST and saved_search_pk:
            request.user.seeker_searches.filter(url=request.path).update(default=False)
            request.user.seeker_searches.filter(pk=saved_search_pk, url=request.path, querystring=qs).update(default=True)
        elif '_unset' in request.POST and saved_search_pk:
            request.user.seeker_searches.filter(url=request.path).update(default=False)
        elif '_delete' in request.POST and saved_search_pk:
            request.user.seeker_searches.filter(pk=saved_search_pk, url=request.path, querystring=qs).delete()
            return redirect(request.path)
        return redirect('%s?%s' % (request.path, post_qs))

    def check_permission(self, request):
        """
        Check to see if the user has permission for this view. This method may optionally return an ``HttpResponse``.
        """
        if self.permission and not request.user.has_perm(self.permission):
            raise Http404

    def dispatch(self, request, *args, **kwargs):
        """
        Overridden to perform permission checking by calling ``self.check_permission``.
        """
        resp = self.check_permission(request)
        if resp is not None:
            return resp
        return super(SeekerView, self).dispatch(request, *args, **kwargs)

