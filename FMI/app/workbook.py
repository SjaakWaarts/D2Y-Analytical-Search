
import logging
import json
import seeker.esm as esm
import dhk_app.recipe_scrape as recipe_scrape
import app.aws as aws
import app.wb_excel as wb_excel
import FMI.settings
from FMI.settings import BASE_DIR, ES_HOSTS, MEDIA_BUCKET, MEDIA_URL
from FMI.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


# A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
# in the template this is translated into HTML tables, rows, cells and div elements


# Chart Syntax
# "chart_name"          : <chart_properties>
# <chart_properties>    : <chart_type> <chart_title> <data_type> <controls>? <help>? <listener>? <transpose>? <X_facet> <Y_facet>? <Z_facet>? <options>?
# <chart_type>          : 'chart_type' : <google chart types> | <d3.js chart types>
# <chart_title>         : 'chart_title' : "chart title"
# <data_type>           : 'facet' | 'aggr' | 'hits' | 'topline'
# <controls>            : [ <google chart controls> | 'tile_layout_select' ]
# <google chart controls> : 'CategoryFilter', 'ChartRangeFilter', 'DateRangeFilter', 'NumberRangeFilter', 'StringFilter'
# <options>             : <google chart options>
# <google chart options> : 'width', 'height', 'colors', 'legend', 'bar', <vAxis>, <hAxis>, 'seriesType', <series>
# <transpose>           : True | False
# <X_facet>, <Y-facet> < Z_facet> : <facet>
#
# <facet>               : <field> <label> <total> <type> <question> <answers> <values> <metric> <mean> <order>
# <type>                : 'date'
# <metric>              : <ElasticSearch metric>
# <ElasticSearch metric>: 'doc_count', 'prc'
# <order>               : <ElasticSearch order>
# <ElasticSearch order> : '_count'|'_key' 'asc'|'desc'
#
# <answers>             : [ <answer>* ]
# <answer>              : <string> | <number> (<range>) | {<mapping>*}
# <range>               : <sign>, <string>|<number>
# <mapping>             : <to value> : [<from value>*] | 'single' | 'a-mean' : *|+ | 'a-wmean' : *|+ 'a-sum': x|+|- | 'q-mean' : *|+
# <aggr_type>           : * answer mean replace single, ** question+answer mean replace single, '+' means add                       
#
# <values>              : [ <value>* ]
# <value>               : <string> | <number> (<range>) | {<mapping>*}
# <range>               : <sign>, <string>|<number>
# <mapping>             : <to value> : [<from value>*] | {'layout' : 'series'|'categories'} | 'v-mean' : *|+ | 'v-wmean' : *|+ 'v-sum': *|+|top-n
#
# Mean can be the average of the different series within a category, type=answer
# Mean can be the average of a serie of all categores, type=question
# The mean can be shown as its own serie, layout=serie
# The mean can be shown as its own category, layout=category
# The mean can be catured as meta_data and shown in the header, layout=header
# <mean>                : <type>, <layout>
# <type>                : 'answer', 'question'
# <layout>              : 'category', 'serie', 'header'
# 

logger = logging.getLogger(__name__)

class Workbook():
    es_index = None
    workbook = None
    es_index = None
    properties = None

    def __init__(self, es_index):
        self.es_index = es_index
        self.workbook = wb_excel.workbooks[es_index]
        self.es_index = self.workbook['es_index']

    def aggs(self, facets):
        es_host = ES_HOSTS[0]
        s, search_q = esm.setup_search()
        search_filters = search_q["query"]["bool"]["filter"]
        search_aggs = search_q["aggs"]
        search_q['size'] = 0
        for facet, facet_conf in facets.items():
            field = facet
            if facet_conf.get('keyword', True):
                field = field + '.keyword'
            options = facet_conf.get('options', {})
            terms_agg = {'terms': {"field": field, **options}}
            nested = facet_conf.get('nested', None)
            search_aggs[facet] = esm.add_agg_nesting(field, nested, terms_agg)
        results = esm.search_query(es_host, self.es_index['index'], search_q)
        results = json.loads(results.text)
        aggs = results.get('aggregations', {})
        return aggs

    def get_field_type(self, field):
        properties = self.es_index
        for sub_field in field.split('.'):
            properties = properties['properties']
            if sub_field in properties:
                properties = properties[sub_field]
        field_type = properties.get('type', None)
        return field_type

