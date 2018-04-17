
import glob, os
from elasticsearch_dsl.utils import AttrList, AttrDict
#from seeker.templatetags.seeker import seeker_format
from app.templatetags.seeker import seeker_format
import collections
import inspect
from collections import OrderedDict
import elasticsearch_dsl as dsl
from django.utils.html import escape
from django.template import loader, Context, RequestContext
from django.utils.safestring import mark_safe


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
        value = result['_source'].get(self.field, None)
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
            url = result.get('url', "")
        if self.field in self.view.urlfields:
            if value:
                url = self.view.urlfields[self.field].format(value.replace(' ', '-').lower())
            if url == "":
                url = result['url']

        keys = []

        template_name = 'app/seeker/column.html'
        if type(value) == AttrList or type(value) == list:
            template_name = 'app/seeker/columnlist.html'
        elif type(value) == AttrDict or type(value) == dict:
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
            elif value.startswith("<html"):
                template_name = 'app/seeker/columntextarea.html'
            #elif len(value) > 80:
            #    template_name = 'app/seeker/columntextarea.html'
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
        value = result['_source'].get(self.field, None)
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



class LinksColumn (Column):
    nestedfacet = None

    def __init__(self, field, label=None, sort=None, value_format=None, template=None, header=None, export=True, highlight=None):
        sort = {field+".name" : {"order" : "asc"}}
        super(LinksColumn, self).__init__(field, label, sort, value_format, template, header, export, highlight)

    def render(self, result, facets, **kwargs):
        value = result['_source'].get(self.field, None)
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

        value2 = AttrList([])
        if value:
            for v in value:
                child_found = v.get('child_found', False)
                value2.append((v['name'], v['url'], child_found))
        value = value2

        params = {
            'result': result,
            'field': self.field,
            'value': value,
            'highlight': highlight,
            'view': self.view,
            'query': self.view.get_keywords_q(),
        }

        params.update(self.context(result, **kwargs))
        template_name = 'app/seeker/columnanchor.html'

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



