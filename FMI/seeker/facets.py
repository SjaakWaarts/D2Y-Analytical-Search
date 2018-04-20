from django.conf import settings
from elasticsearch_dsl import Search, A, Q
from elasticsearch_dsl.utils import AttrList, AttrDict
from collections import OrderedDict
import functools
import operator
from .mapping import DEFAULT_ANALYZER

class Facet (object):
    field = None
    label = None
    visible_pos = 1
    keywords_input = 'keywords_k'
    search_fields = None

    template = getattr(settings, 'SEEKER_DEFAULT_FACET_TEMPLATE', 'app/seeker/facets/terms.html')

    def __init__(self, field, label=None, name=None, description=None, template=None, visible_pos = 1, **kwargs):
        self.field = field
        self.label = label or self.field.replace('_', ' ').replace('.raw', '').replace('.', ' ').capitalize()
        #self.name = (name or self.field).replace('.raw', '').replace('.', '_')
        self.name = (name or self.field).replace('.raw', '')
        self.template = template or self.template
        self.description = description
        self.visible_pos = visible_pos
        self.kwargs = kwargs

    # required by KeywordFacet for its filter search
    def set_search_fields(self, search_fields):
        self.search_fields = search_fields

    # use apply for chart and tile aggregation
    # normally this is the same as for facet aggregation, however it migh differ (Nested)
    def aggr(self, search, agg_name, aggs_stack, **extra):
        self.apply(search, agg_name, aggs_stack, **extra)
        return search 

    # term
    #   agg_name = self.name (facet)
    #   search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1)
    # term * term (chart)
    #   agg_name = chart_name
    #   search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #                      bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1)
    # term * term * term (chart)
    #   agg_name = chart_name
    #       search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #                       bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1).\
    #                           bucket(y_field, 'terms', field=y_field, size=40, min_doc_count=1)
    # term * nestedterm - q/a (chart)
    #   agg_name = chart_name
    #        search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #                   bucket(nestedfield, 'nested', path=nestedfield).\
    #                       bucket('question', 'terms', field=nestedfield+".question.keyword", size=40, min_doc_count=1).\
    #                           bucket('answer', 'terms', field=nestedfield+".answer.keyword", size=40, min_doc_count=1)
    # term * optionterm - val (chart)
    #   agg_name = chart_name
    #        search.aggs.bucket(self.name, 'nested', path=self.nestedfield).bucket('val', 'terms', field=self.field, size=40, min_doc_count=1)
    # term * optionterm
    #   agg_name = chart_name
    #        search.aggs.bucket(self.name, 'nested', path=self.nestedfield).\
    #                    bucket('question', 'terms', field=self.nestedfield+".question.keyword", size=40, min_doc_count=1).\
    #                        bucket('answer', 'terms', field=self.nestedfield+".answer.keyword", size=40, min_doc_count=1)
    # use apply for facet aggregation
    def apply(self, search, agg_name, aggs_stack, **extra):
        return search

    def filter(self, search, values):
        return search

    def data(self, response):
        aggregations = response.get('aggregations', {})
        try:
            #print("Facet.data", self.name)
            #return response.aggregations[self.name].to_dict()
            return aggregations[self.name]
        except:
            if self.name in aggregations:
                pass
                #print("Facet.data failed", response.aggregations[self.name])
            else:
                pass
                #print("Facet.data failed, no aggregations")
            return {}

    #def get_key(self, bucket):
    #    return bucket.get('key')

    def get_metric(self, bucket):
        return bucket['doc_count']

    def get_answer_total_calc(self, chart_facet):
        # mean type: '-' mean no mean, '+' add a mean, '*' replace mean
        total_calc = {}
        if 'answers' in chart_facet:
            total_calc = {'single':'+'}
            for answer in chart_facet['answers']:
                if type(answer) == dict:
                    for aggr, aggr_type in answer.items():
                        if aggr in ['a-sum','a-mean','a-wmean']:
                            total_calc[aggr] = aggr_type
        else:
            total_calc = {'single':'+'}
        return total_calc

    def __match_key(self, key, answer_key):
        found = False
        if type(answer_key) == str or type(answer_key) == int:
            if key == answer_key:
                found = True
        elif type(answer_key) == list:
            if key in answer_key:
                found = True
        return found


    def get_answer_hit(self, field, chart_facet):
        return field


    def get_answer(self, key, chart_facet):
        answers = []
        if 'answers' in chart_facet:
            answers = chart_facet['answers']
        if len(answers) == 0:
            return key
        # check on exclude, include or all and special mappings
        all = True
        exclude = False
        include = False
        for answer in answers:
            if type(answer) == str or type(answer) == int:
                all = False
                answer_key = answer
                if self.__match_key(key, answer_key):
                    include = True
            elif type(answer) == tuple:
                options = answer[0]
                answer_key = answer[1]
                if options != '!':
                    all = False
                    if options == '=':
                        if self.__match_key(key, answer_key):
                            include = True
                        if answer_key == '*':
                            include = True
                else:
                    if self.__match_key(key, answer_key):
                        exclude = True
            elif type(answer) == dict:
                for to_key, from_key in answer.items():
                    if not (to_key in ['a-sum', 'a-mean', 'a-wmean', 'q-mean']):
                        all = False
                        if self.__match_key(key, from_key):
                            key = to_key
                            include = True
        if exclude or not(all or include):
            key = None
        return key

    def get_value_total_calc(self, chart_facet):
        # mean type: '-' mean no mean, '+' add a mean, '*' replace mean OR
        # layout: series or categories
        total_calc = {}
        if 'values' in chart_facet:
            series = True
            for answer in chart_facet['values']:
                if type(answer) == dict:
                    for aggr, aggr_type in answer.items():
                        if aggr in ['v-sum','v-mean','v-wmean', 'layout']:
                            total_calc[aggr] = aggr_type
                            if aggr_type == '*':
                                series = False
                            if aggr == 'layout':
                                series = False
            if series:
                total_calc = {'layout': 'series'}
        else:
            total_calc = {'v-sum':'*'}
        return total_calc

    def get_value_key(self, value_key, chart_facet):
        values = []
        # in case no values in facet, the default is summation
        if 'values' in chart_facet:
            values = chart_facet['values']
        if len(values) == 0:
            return value_key                 
        # check on exclude, include or all and special mappings
        all = True
        exclude = False
        include = False
        for value in values:
            if type(value) == str or type(value) == int:
                all = False
                value_key2 = value
                if self.__match_key(value_key, value_key2):
                    include = True
            elif type(value) == tuple:
                options = value[0]
                value_key2 = value[1]
                if options != '!':
                    all = False
                    if options == '=':
                        if self.__match_key(value_key, value_key2):
                            include = True
                        if value_key2 == '*':
                            include = True
                else:
                    if self.__match_key(value_key, value_key2):
                        exclude = True  
            elif type(value) == dict:
                for to_key, from_key in value.items():
                    if not (to_key in ['v-sum', 'v-mean', 'v-wmean', 'layout']):
                        all = False
                        if self.__match_key(value_key, from_key):
                            value_key = to_key
                            include = True
        if exclude or not(all or include):
            value_key = None
        return value_key

    def decoder(self, X_key, Y_key):
        return Y_key

    def buckets(self, aggregations):
        #for b in self.data(response).get('buckets', []):
        #    yield self.get_key(b), b.get('doc_count')
        # preserve sequence
        buckets = OrderedDict()
        for bucket in aggregations['buckets']:
            buckets[bucket['key']] = bucket
        return buckets

    def valbuckets(self, bucket):
        valbuckets = OrderedDict({"Total" : bucket})
        return valbuckets

class TermsFacet (Facet):

    def __init__(self, field, **kwargs):
        self.filter_operator = kwargs.pop('filter_operator', 'or')
        super(TermsFacet, self).__init__(field, **kwargs)

    def _get_aggregation(self, reverse_nested, **extra):
        if reverse_nested == False:
            params = {
                'field': self.field,
                'size' : 40,
                'min_doc_count': 1
                }
            params.update(self.kwargs)
            params.update(extra)
            return A('terms', **params)
        else:
            params = {
                'aggs' : {
                    self.field : {
                        'terms' : {
                            "field" : self.field,
                            "size"  : 40,
                            "min_doc_count" : 1
                            }
                        }
                    }
                }
            params.update(self.kwargs)
            params.update(extra)
            return A('reverse_nested', **params)

    # use apply for aggregation (facet, chart, tile)
    def apply(self, search, agg_name, aggs_stack, **extra):
        #search.aggs[self.name] = self._get_aggregation(**extra)
        reverse_nested = False;
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            t = type(aggs_tail)
            if t.name == 'nested':
                reverse_nested = True
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
                t = type(aggs_tail)
                if t.name == 'nested':
                    reverse_nested = True
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
            #aggs_tail.bucket(self.name, 'terms', field=self.field, size=40, min_doc_count=1)
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(reverse_nested, **extra)
        #if extra:
        #    aggs_stack[agg_name].append(list(extra['aggs'].keys())[0])
        #search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1)
        d = search.to_dict()
        return search

    ## use apply for facet tile aggregation
    #def apply_tile(self,  search, chart_name, x_field, y_field, **extra):
    #    agg_name = self.name+'_'+chart_name
    #    #if y_field == None:
    #    #    search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #    #                    bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1)
    #    #else:
    #    #    search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #    #                    bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1).\
    #    #                        bucket(y_field, 'terms', field=y_field, size=40, min_doc_count=1)
    #    search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1)
    #    aggs_tail = search.aggs[agg_name]
    #    #search.aggs[agg_name].bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1)
    #    aggs_tail.bucket(x_field, 'terms', field=x_field, size=40, min_doc_count=1)
    #    aggs_tail = aggs_tail.aggs[x_field]
    #    if y_field:
    #        #search.aggs[agg_name].aggs[x_field].bucket(y_field, 'terms', field=y_field, size=40, min_doc_count=1)
    #        aggs_tail.bucket(y_field, 'terms', field=y_field, size=40, min_doc_count=1)
    #    return search

    ##use apply for facet aggregation
    #def apply_tile_nested(self, search, agg_name, nestedfield, **extra):
    #    #search.aggs[self.name] = self._get_aggregation(**extra)
    #    search.aggs.bucket(agg_name, 'terms', field=self.field, size=40, min_doc_count=1).\
    #                    bucket(nestedfield, 'nested', path=nestedfield).\
    #                        bucket('question', 'terms', field=nestedfield+".question.keyword", size=40, min_doc_count=1).\
    #                            bucket('answer', 'terms', field=nestedfield+".answer.keyword", size=40, min_doc_count=1)
    #    return search


    def filter(self, search, values):
        if len(values) > 1:
            if self.filter_operator.lower() == 'and':
                filters = [Q('term', **{self.field: v}) for v in values]
                return search.query(functools.reduce(operator.and_, filters))
            else:
                return search.filter('terms', **{self.field: values})
        elif len(values) == 1:
            return search.filter('term', **{self.field: values[0]})
        return search

    def buckets(self, aggregations):
        # preserve sequence
        buckets = OrderedDict()
        for bucket in aggregations['buckets']:
            buckets[bucket['key']] = bucket
        return buckets

class NestedFacet (TermsFacet):
    template = 'app/seeker/facets/nestedterms.html'
    rangeon = True
    rangemin = 0.20
    rangemax = 0.0
    nestedfield = ''
    sort_nested_filter = None

    def __init__(self, field, nestedfield=None, **kwargs):
        self.nestedfield = nestedfield
        super(NestedFacet, self).__init__(field, **kwargs)

    #"AR3": {
    #  "nested": {
    #    "path": "AR"
    #  },
    #  "aggs": {
    #    "val": {
    #      "terms": {
    #        "field": "AR.val.keyword"
    #      },
    #      "aggs": {
    #        "prc": {
    #          "avg": {
    #            "field": "AR.prc"
    #          }
    #        }
    #      }
    #    }
    #  }
    #}

    def _get_chart_aggregation(self, **extra):
        nested_params = {
            'path': self.nestedfield,
            'aggs': {
                'val' : {
                    'terms': {
                        'field': self.nestedfield + '.val.keyword',
                        "size"  : 40,
                        "min_doc_count" : 1
                        },
                    'aggs': {
                        'prc' : {
                            'avg' : {
                                'field': self.nestedfield + '.prc'
                                }
                            }
                        }
                    }
                }
            }
        return A('nested', **nested_params)

    # use apply for chart and tile aggregation
    # normally this is the same as for facet aggregation, however it migh differ (Nested)
    def aggr(self, search, agg_name, aggs_stack, **extra):
        #search.aggs.bucket(agg_name, 'nested', path=self.nestedfield).bucket('val', 'terms', field=self.field, size=40, min_doc_count=1)
        if agg_name in aggs_stack:
            #aggs_tail = search.aggs[self.name]
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_stack[agg_name].append('prc')
        aggs_tail.aggs[sub_agg_name] = self._get_chart_aggregation(**extra)
        d = search.to_dict()
        return search

    #"aggs": {
    #  "smell": {
    #    "terms": {
    #      "field": "smell.keyword"
    #    }
    #  },
    #  "texture_p": {
    #    "nested": {
    #      "path": "texture_p"
    #    },
    #    "aggs": {
    #      "texture": {
    #        "terms": {
    #          "field": "texture_p.val.keyword"
    #        }
    #      }
    #    }
    #  }
    #}

    def _get_facet_aggregation(self, **extra):
        params = {
            'field': self.field,
            'size' : 40,
            'min_doc_count': 1
            }
        params.update(self.kwargs)
        params.update(extra)
        nested_params = {
            'path': self.nestedfield,
            'aggs': {
                'val' : {
                    'terms' : params
                    }
                }
            }
        return A('nested', **nested_params)

    # use apply for facet aggregation
    def apply(self, search, agg_name, aggs_stack, **extra):
        #search.aggs.bucket(agg_name, 'nested', path=self.nestedfield).bucket('val', 'terms', field=self.field, size=40, min_doc_count=1)
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_stack[agg_name].append('val')
        aggs_tail.aggs[sub_agg_name] = self._get_facet_aggregation(**extra)
        d = search.to_dict()
        return search


    def filter(self, search, values):
        self.sort_nested_filter = None
        query = None
        field = self.nestedfield
        field_val = field+".val.keyword"
        field_prc = field+".prc"
        if len(values) > 1:
            filters = []
            terms_filter = {field_val : []}
            for val in values:
                terms_filter[field_val].append(val)
                sub_filter = [{"term": {field_val: val}}, {"range": {field_prc: {"gte": self.rangemin}}}]
                filter = {"path": field, "query" : {"bool" : {"must": sub_filter}}}
                search = search.filter('nested', **filter)
            nested_filter = [{"terms": terms_filter}, {"range": {field_prc: {"gte": self.rangemin}}}]
            query = {"bool" : {"must": nested_filter}}
        elif len(values) == 1:
            sub_filter = [{"term": {field_val: values[0]}}, {"range": {field_prc: {"gte": self.rangemin}}}]
            filter = {"path": field, "query" : {"bool" : {"must": sub_filter}}}
            query = {"bool" : {"must" : sub_filter}}
            self.sort_nested_filter = query
            return search.filter('nested', **filter)
        self.sort_nested_filter = query
        return search

    def sort(self):
        return self.sort_nested_filter

    def buckets(self, aggregations):
        # preserve sequence
        buckets = OrderedDict()
        for prcbucket in aggregations['val']['buckets']:
            buckets[prcbucket['key']] = prcbucket
        return buckets

    def valbuckets(self, prcbucket):
        # preserve sequence
        calcbuckets = OrderedDict()
        calcbuckets['prc'] = prcbucket['prc']
        return calcbuckets

    def get_metric(self, bucket):
        if 'prc' in bucket:
            prc = bucket['prc']['value']
        else:
            prc = bucket['value']
        return prc

    def get_answer_hit(self, field, chart_facet):
        Y_key = None
        if 'answers' in chart_facet:
            for attr in field:
                if attr['val'] == chart_facet['answers'][0]:
                    Y_key = attr['prc']
                    continue
        return Y_key


class OptionFacet (TermsFacet):
    template = 'app/seeker/facets/optionterms.html'
    rangeon = True
    rangemin = 0.25
    rangemax = 0.0
    nestedfield = ''
    sort_nested_filter = None

    def __init__(self, field, nestedfield=None, **kwargs):
        self.nestedfield = nestedfield
        super(OptionFacet, self).__init__(field, **kwargs)

    def _get_aggregation(self, **extra):
        #params = {
        #    'path': self.nestedfield,
        #    'aggs': {
        #        'question' : {
        #            'terms': {
        #                "field" : self.nestedfield+".question.keyword",
        #                "size"  : 40,
        #                "min_doc_count" : 1
        #                },
        #            'aggs' : {
        #                "answer" : {
        #                    'terms' : {
        #                        "field" : self.nestedfield+".answer.keyword",
        #                        "size"  : 40,
        #                        "min_doc_count" : 1
        #                        }
        #                    }
        #                }
        #            }
        #        }
        #    }
        #params.update(self.kwargs)
        #params.update(extra)
        params = {
            'field': self.nestedfield+".answer.keyword",
            'size' : 40,
            'min_doc_count': 1
            }
        params.update(self.kwargs)
        params.update(extra)
        nested_params = {
            'path': self.nestedfield,
            'aggs': {
                'question' : {
                    'terms': {
                        "field" : self.nestedfield+".question.keyword",
                        "size"  : 40,
                        "min_doc_count" : 1
                        },
                    'aggs' : {
                        "answer" : {
                            'terms' : params
                                }
                            }
                        }
                    }
                }
        return A('nested', **nested_params)

    # use apply for aggregation (facet, chart, tile)
    def apply(self, search, agg_name, aggs_stack, **extra):
        #search.aggs.bucket(agg_name, 'nested', path=self.nestedfield).\
        #               bucket('question', 'terms', field=self.nestedfield+".question.keyword", size=40, min_doc_count=1).\
        #                   bucket('answer', 'terms', field=self.nestedfield+".answer.keyword", size=40, min_doc_count=1)
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_stack[agg_name].append('question')
        aggs_stack[agg_name].append('answer')
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(**extra)
        d = search.to_dict()
        return search

    def filter(self, search, values):
        self.sort_nested_filter = None
        query = None
        field = self.nestedfield
        q_field = field+".question.keyword"
        a_field = field+".answer.keyword"
        filters = []
        terms_filter = {q_field : []}
        for val in values:
            m = val.find('^')
            q = val[:m]
            a = val[m+1:]
            terms_filter[q_field].append(q)
            sub_filter = [{"term": {q_field: q}}, {"term": {a_field: a}}]
            filter = {"path": field, "query" : {"bool" : {"must": sub_filter}}}
            search = search.filter('nested', **filter)
        nested_filter = [{"terms": terms_filter}]
        query = {"bool" : {"must": nested_filter}}
        self.sort_nested_filter = query
        return search

    def sort(self):
        return self.sort_nested_filter

    def buckets(self, aggregations):
        # preserve sequence
        buckets = OrderedDict()
        for bucket in aggregations['question']['buckets']:
            buckets[bucket['key']] = bucket
        return buckets

    def valbuckets(self, bucket):
        # preserve sequence
        valbuckets = OrderedDict()
        for subbucket in bucket['answer']['buckets']:
            valbuckets[subbucket['key']] = subbucket
        return valbuckets

    def get_answer_hit(self, field, chart_facet):
        Y_key = None
        if 'answers' in chart_facet:
            for attr in field:
                if attr['question'] == chart_facet['answers'][0]:
                    Y_key = attr['answer']
                    continue
        return Y_key


class KeywordFacet (TermsFacet):
    template = 'app/seeker/facets/keyword.html'
    keywords_input = ''
    keywords_text = ''
    keywords_k = []
    read_keywords = ''
    initial = ""

    def __init__(self, field, input=None, initial=None, **kwargs):
        self.keywords_input = input
        self.initial = initial
        super(KeywordFacet, self).__init__(field, **kwargs)

    #"aggs": {
    #  "perfume": {
    #    "terms": {
    #      "field": "perfume.keyword"
    #    },
    #    "aggs": {
    #      "keyfig": {
    #        "filters": {
    #          "filters": {
    #            "bottle": {
    #              "multi_match": {
    #                "query": "bottle",
    #                "fields": [
    #                  "review"
    #                ]
    #              }
    #            },
    #            "floral": {
    #              "multi_match": {
    #                "query": "floral",
    #                "fields": [
    #                  "review"
    #                ]
    #              }
    #            }
    #          }
    #        }
    #      }
    #    }
    #  },

    def _get_aggregation(self, **extra):
        params = {}
        params.update(extra)
        return A('filters', **params)

    # use apply for aggregation (facet, chart, tile)
    def apply(self, search, agg_name, aggs_stack, **extra):
        # in case no keywords specified, just return the original search
        if len(self.keywords_k) == 0:
           return search
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        if extra == {}:
            body_kf = {}
            for kf in self.keywords_k:
                body_kf[kf] = {'multi_match' : {'query': kf, 'analyzer': DEFAULT_ANALYZER, 'fields': self.search_fields}}
            extra['filters']=body_kf
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(**extra)
        d = search.to_dict()
        return search

    def data(self, response):
        aggregations = response.get('aggregations', {})
        try:
            #print("KeywordFacet.data", self.name)
            return aggregations[self.name]
        except:
            if self.name in aggregations:
                pass
                #print("KeywordFacet.data failed", aggregations[self.name])
            else:
                pass
                #print("KeywordFacet.data failed, no aggregations")
            return {'keyword': 'Enter your keywords'}

    def buckets(self, aggregations):
        buckets = OrderedDict()
        if type(aggregations['buckets']) == AttrDict  or type(aggregations['buckets']) == dict:
            for keyword, bucket in aggregations['buckets'].items():
                bucket['key'] = keyword
                buckets[keyword] = bucket
        else:
            buckets = {}
        return buckets

class GlobalTermsFacet (TermsFacet):

    def apply(self, search, agg_name, aggs_stack, **extra):
        top = A('global')
        top[self.field] = self._get_aggregation(**extra)
        search.aggs[self.field] = top
        d = search.to_dict()
        return search

    def data(self, response):
        aggregations = response.get('aggregations', {})
        print("GlobalTemrsFacet.data", self.name)
        return aggregations[self.field][self.field]


class YearHistogram (Facet):
    template = 'app/seeker/facets/year_histogram.html'

    def _get_aggregation(self, **extra):
        params = {
            'field': self.field,
            'interval': 'year',
            'format': 'yyyy',
            'min_doc_count': 1,
            'order': {'_key': 'desc'},
        }
        params.update(self.kwargs)
        params.update(extra)
        return A('date_histogram', **params)

    def apply(self, search, agg_name, aggs_stack, **extra):
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(**extra)
        d = search.to_dict()
        return search

    def filter(self, search, values):
        if len(values) > 0:
            filters = []
            for val in values:
                kw = {
                    self.field: {
                        'gte': '%s-01-01T00:00:00' % val,
                        'lte': '%s-12-31T23:59:59' % val,
                    }
                }
                filters.append(Q('range', **kw))
            search = search.query(functools.reduce(operator.or_, filters))
        return search

    def get_key(self, bucket):
        return bucket.get('key_as_string')

    def buckets(self, aggregations):
        buckets = OrderedDict()
        # use string format as key and overwrite the key attribute as well
        for bucket in aggregations['buckets']:
            key = bucket['key_as_string']
            bucket['key'] = key
            buckets[key] = bucket
        return buckets

class MonthHistogram (Facet):
    template = 'app/seeker/facets/year_histogram.html'

    def _get_aggregation(self, **extra):
        params = {
            'field': self.field,
            'interval': 'month',
            'format': 'yyyy-MM',
            'min_doc_count': 1,
            'order': {'_key': 'desc'},
        }
        params.update(self.kwargs)
        params.update(extra)
        return A('date_histogram', **params)

    def apply(self, search, agg_name, aggs_stack, **extra):
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(**extra)
        d = search.to_dict()
        return search

    def filter(self, search, values):
        if len(values) > 0:
            filters = []
            for val in values:
                kw = {
                    self.field: {
                        'gte': '%s-01T00:00:00' % val,
                        'lte': '%s-31T23:59:59' % val,
                    }
                }
                filters.append(Q('range', **kw))
            search = search.query(functools.reduce(operator.or_, filters))
        return search

    def get_key(self, bucket):
        return bucket.get('key_as_string')

    def buckets(self, aggregations):
        buckets = OrderedDict()
        # use string format as key and overwrite the key attribute as well
        for bucket in aggregations['buckets']:
            key = bucket['key_as_string']
            bucket['key'] = key
            buckets[key] = bucket
        return buckets

class DayHistogram (Facet):
    template = 'app/seeker/facets/year_histogram.html'

    def _get_aggregation(self, **extra):
        params = {
            'field': self.field,
            'interval': 'day',
            'format': 'yyyy-MM-dd',
            'min_doc_count': 1,
            'order': {'_key': 'desc'},
        }
        params.update(self.kwargs)
        params.update(extra)
        return A('date_histogram', **params)

    def apply(self, search, agg_name, aggs_stack, **extra):
        if agg_name in aggs_stack:
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_tail.aggs[sub_agg_name] = self._get_aggregation(**extra)
        d = search.to_dict()
        return search

    def filter(self, search, values):
        if len(values) > 0:
            filters = []
            for val in values:
                kw = {
                    self.field: {
                        'gte': '%sT00:00:00' % val,
                        'lte': '%sT23:59:59' % val,
                    }
                }
                filters.append(Q('range', **kw))
            search = search.query(functools.reduce(operator.or_, filters))
        return search

    def get_key(self, bucket):
        return bucket.get('key_as_string')

    def buckets(self, aggregations):
        buckets = OrderedDict()
        # use string format as key and overwrite the key attribute as well
        for bucket in aggregations['buckets']:
            key = bucket['key_as_string']
            bucket['key'] = key
            buckets[key] = bucket
        return buckets


class RangeFilter (Facet):
    template = 'app/seeker/facets/range.html'

    def _get_chart_aggregation(self, **extra):
        params = {
            'field': self.field,
            }
        params.update(self.kwargs)
        params.update(extra)
        return A('avg', **params)

    # use apply for chart and tile aggregation
    # normally this is the same as for facet aggregation, however it migh differ (Nested)
    def aggr(self, search, agg_name, aggs_stack, **extra):
        #search.aggs.bucket(agg_name, 'nested', path=self.nestedfield).bucket('val', 'terms', field=self.field, size=40, min_doc_count=1)
        if agg_name in aggs_stack:
            #aggs_tail = search.aggs[self.name]
            aggs_tail = search.aggs[agg_name]
            for sub_agg_name in aggs_stack[agg_name][1:]:
                aggs_tail = aggs_tail.aggs[sub_agg_name]
            aggs_stack[agg_name].append(self.name)
            sub_agg_name = self.name
        else:
            aggs_tail = search
            aggs_stack[agg_name] = [agg_name]
            sub_agg_name = agg_name
        aggs_stack[agg_name].append('prc')
        aggs_tail.aggs[sub_agg_name] = self._get_chart_aggregation(**extra)
        d = search.to_dict()
        return search


    def apply(self, search, agg_name, aggs_stack, **extra):
        #params = {
        #    'field': self.field,
        #    'keyed': True,
        #    'ranges': [{'to': 25}, {'from':25, 'to': 50}, {'from':50, 'to': 75}, {'from':75}],
        #}
        params = {
            'field': self.field,
            'interval': 10,
        }
        params.update(self.kwargs)
        params.update(extra)
        search.aggs[self.name] = A('histogram', **params)
        d = search.to_dict()
        return search

    def filter(self, search, values):
        if len(values) == 2:
            r = {}
            if values[0].isdigit():
                r['gte'] = values[0]
            if values[1].isdigit():
                r['lte'] = values[1]
            search = search.filter('range', **{self.field: r})
        return search

    def buckets(self, aggregations):
        #for b in self.data(response).get('buckets', []):
        #    yield self.get_key(b), b.get('doc_count')
        # preserve sequence
        buckets = OrderedDict()
        buckets[self.field] = aggregations['value']
        return buckets

    def get_metric(self, bucket):
        return bucket

