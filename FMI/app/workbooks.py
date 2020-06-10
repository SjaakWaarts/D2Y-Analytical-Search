"""
Definition of models.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.views.generic.base import TemplateView

# Create your models here.
import queue
import datetime
from collections import OrderedDict
from pandas import DataFrame

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl import Date, Double, Long, Integer, Boolean
from elasticsearch_dsl.connections import connections

import seeker
import FMI.settings


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


class PostWorkbook:
    dashboard = {
        'category_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Category / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "post_category_id.keyword",
                'label'   : "Category" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "subject_keyword_table" : {
            'chart_type': "Table",
            'chart_title' : "Subject / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "subject.keyword",
                'label'   : "Subject" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "facet_keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "facet_cust_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Customers Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_cust",
                'label'   : "Customers" },
            },
        "facet_comp_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Competitors Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_comp",
                'label'   : "Competitors" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Month Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM'},
                },
            },
        }

    dashboard_layout = OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"]]
    dashboard_layout['rows2'] = [["facet_cust_pie", "facet_comp_pie", "facet_keyword_pie"]]
    dashboard_layout['rows3'] = [["category_keyword_table", "subject_keyword_table"]]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ] 

    workbooks = {
        "initial" : {
            'charts'        : dashboard,
            'storyboards'   : {'initial' : storyboard},
            }
        }

class PageWorkbook:
    dashboard = {
        'sub_site_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "SubSite / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "sub_site.keyword",
                'label'   : "Category" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "section_keyword_table" : {
            'chart_type': "Table",
            'chart_title' : "Section / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "section.keyword",
                'label'   : "Subject" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "facet_keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "facet_cust_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Customers Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_cust",
                'label'   : "Customers" },
            },
        "facet_comp_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Competitors Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_comp",
                'label'   : "Competitors" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Month Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM'},
                },
            },
        }

    dashboard_layout = OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"]]
    dashboard_layout['rows2'] = [["facet_cust_pie", "facet_comp_pie", "facet_keyword_pie"]]
    dashboard_layout['rows3'] = [["sub_site_keyword_table", "section_keyword_table"]]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ] 

    workbooks = {
        "initial" : {
            'charts'        : dashboard,
            'storyboards'   : {'initial' : storyboard},
            }
        }

class ScentemotionWorkbook:

    dashboard = {
        'region_olfactive_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Region / Olfactive Ingr Count",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "region.keyword",
                'label'   : "Region"},
            'Y_facet'     : {
                'field'   : "olfactive.keyword",
                'label'   : "Olfactive"},
            },
        "olfactive_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Olfactive Ingr Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "olfactive.keyword",
                'label'   : "Olfactive" },
            },
        "olfactive_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Olfactive Ingr Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "olfactive.keyword",
                'label'   : "Olfactive" },
            },
        "cand_mood_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Mood Top Candidates",
            'data_type'  : "hits",
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "mood",
                'question': "Mood",
                "answers" : ["Happy","Relaxed"],
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Mood"
                },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {2: {"type": 'line'}, 3: {"type": 'line'}}
                },
            },
        "cand_smell_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Smell Top Candidates",
            'data_type'  : "hits",
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "smell",
                'question': "Smell",
                "answers" : ["Clean","Natural"],
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Mood"
                },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {2: {"type": 'line'}, 3: {"type": 'line'}}
                },
            },
        "cand_intensity_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Intensity Top Candidates",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'select' : {'colsort': None, 'rowcolfilter': ["mood_cand_radar", "smell_cand_radar", "negative_cand_radar", "descriptor_cand_radar"]}},
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "intensity",
                "q-mean"  : True,
                'label'   : "Intensity" },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
                },
            },
        "mood_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Mood",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "mood",
                'question': "Mood",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Mood"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "smell_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Smell",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "smell",
                'question': "Smell",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Smell"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "negative_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Negative",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "negative",
                'question': "Negative",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Negative"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "descriptor_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Descriptor",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "IPC",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptor",
                'question': "Descriptor",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Descriptor"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        }
    dashboard_olfactive = OrderedDict()
    dashboard_olfactive['rows'] = [["region_olfactive_table"], ["olfactive_pie", "olfactive_col"]]

    dashboard_candidates = OrderedDict()
    dashboard_candidates['rows'] = [["cand_mood_col"],["cand_smell_col"],["cand_intensity_col"]]

    dashboard_profile = OrderedDict()
    dashboard_profile['columns'] = [["cand_intensity_col"], ["mood_cand_radar", "smell_cand_radar"], ["negative_cand_radar", "descriptor_cand_radar"]]

    storyboard = [
        {'name' : 'Olfactive',
         'layout'   : dashboard_olfactive,
         },
        {'name' : 'Candidates',
         'layout'   : dashboard_candidates,
         },
        {'name' : 'Profile',
         'layout'   : dashboard_profile,
         },
    ]

    workbooks = {
        "initial" : {
            'charts'        : dashboard,
            'storyboards'   : {'initial' : storyboard},
            }
        }

class StudiesWorkbook:

    dashboard = {
        "cand_emotion_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Emotion Top Candidates",
            'data_type'  : "hits",
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "emotion",
                'question': "Emotion",
                "answers" : ["Addictive","Classic", "Cheap"],
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Emotion"
                },
            'options'     : {
            #      #title   : 'Monthly Coffee Production by Country',
            #      #vAxis   : {title: 'Cups'},
            #      #hAxis   : {title: 'Month'},
                "seriesType" : 'bars',
                "series"  : {3: {"type": 'line'}, 4: {"type": 'line'}}
                },
            },
        "cand_freshness_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Freshness Top Candidates",
            'data_type'  : "hits",
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "freshness",
                "metric"  : "prc",
                "q-mean"  : True,
                'label'   : "Freshness" },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
                },
            },
        "cand_liking_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Liking Top Candidates",
            'data_type'  : "hits",
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "liking",
                'question': "Liking",
                'metric'  : "prc",
                "q-mean"  : True,
                'label'   : "Liking"
                },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
                },
            },
        "hedonics_cand_table" : {
            'chart_type': "Table",
            'chart_title' : "Topline",
            'data_type'  : "topline",
            'controls'    : [],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["suitable_stage_cand_bar", "suitable_stage_cand_radar"], 'select' : {'rowsort': None}},
            'X_facet'     : {
                'fields'  : {
                    "liking" : {
                            'lines'   : {"liking" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                        },
                    },
                },
            'Y_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            #'formatter'  : {
            #    'NumberFormat' : {},
            #    'setColumnProperties'   : {},
            #    'setProperty'   : [],
            #    },
            },
        "suitable_stage_cand_bar" : {
            'chart_type': "BarChart",
            'chart_title' : "Suitable Stage",
            'data_type'  : "hits",
            'transpose'   : True,
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "suitable_stage",
                'question': "Stage",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Stage"
                },
            },
        "suitable_stage_cand_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Suitable Stage",
            'data_type'  : "hits",
            'transpose'   : True,
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "suitable_stage",
                'question': "Stage",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Stage"
                },
            },
        }
    dashboard_olfactive = OrderedDict()
    dashboard_olfactive['rows'] = [["region_olfactive_table"], ["olfactive_pie", "olfactive_col"]]

    dashboard_candidates = OrderedDict()
    dashboard_candidates['rows'] = [["cand_liking_col"],["cand_freshness_col"],["cand_emotion_col"]]

    dashboard_profile = OrderedDict()
    dashboard_profile['columns'] = [["hedonics_cand_table"], ["suitable_stage_cand_bar"],["suitable_stage_cand_radar"]]

    storyboard = [
        {'name' : 'Candidates',
         'layout'   : dashboard_candidates,
         #'active'   : True,
         },
        {'name' : 'Profile',
         'layout'   : dashboard_profile,
         #'active'   : False,
         },
    ]

    workbooks = {
        "initial" : {
            'charts'        : dashboard,
            'storyboards'   : {'initial' : storyboard},
            }
        }

class SurveyWorkbook:

    dashboard_fresh = {
        "cand_emotion_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Candidates / Emotion",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "emotion",
                'question': "Emotion",
                "answers" : ["Addictive","Classic"],
                "values"  : ["Yes", {'v-sum':'*'}],
                "metric"  : "doc_count",
                "a-mean"  : True,
                'label'   : "Emotion"
                },
            'options'     : {
            #      #title   : 'Monthly Coffee Production by Country',
            #      #vAxis   : {title: 'Cups'},
            #      #hAxis   : {title: 'Month'},
                "seriesType" : 'bars',
                "series"  : {2: {"type": 'line'}, 3: {"type": 'line'}}
                },
            },
        "liking_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('=', '*'), ('!', [0,'','0'])],
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            },
        "topline_liking_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate #",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_col",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_emotion_col", "cand_concept_radar", "cand_emotion_radar", "cand_mood_radar"], 'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'lines'   : {"liking.keyword" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                #'NumberFormat' : {1 : {'pattern' : '#.##'},2 : {'pattern' : '#.#'}},
                #'setColumnProperties'   : {1 : {'style': 'font-style:bold; font-size:22px;'}},
                'setProperty'   : [],
                #'setProperty'   : [[2, 1, 'style', 'font-style:bold;'],
                #                   [3, 3, 'background-color', 'red' ],
                #                   [0, 1, 'className', 'benchmark'],
                #                   [1, 1, 'className', 'benchmark'],
                #                   [2, 1, 'className', 'benchmark'],
                #                   [3, 1, 'className', 'benchmark'],
                #                   [4, 1, 'className', 'benchmark'],
                #                   ],
                },
            },
        "freshness_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Freshness Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "freshness",
                'label'   : "Freshness" },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            },
        "topline_freshness_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Freshness - Candidate #",
            'data_type'   : "aggr",
            'base'        : "freshness_blindcode_col",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "freshness",
                'label'   : "Freshness",
                'lines'   : {"freshness" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        "cleanliness_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Cleanliness Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "cleanliness",
                'label'   : "Cleanliness" },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            },
        "suitable_stage_ans_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Suitable Stage Resp Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "suitable_stage",
                "answers" : [],
                "values"  : [],
                'total'   : False,
                'label'   : "Suitable Stage" },
            },
        "suitable_product_ans_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Suitable Product #",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "suitable_product",
                "answers" : [],
                "values"  : [],
                'total'   : False,
                'label'   : "Suitable Product" },
            },
        "emotion_ans_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Emotion #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "emotion",
                "answers" : [],
                "values"  : ["Yes", "No"],
                'total'   : False,
                'label'   : "Emotion" },
            },
        "cand_concept_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Concept",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "concept",
                'question': "Concept",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Concept"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_emotion_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Emotion",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "emotion",
                'question': "Emotion",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Emotion"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_mood_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Mood",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "mood",
                'question': "Mood",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Mood"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "topline_liking_combo" : {
            'chart_type'  : "ComboChart",
            #'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_col",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_emotion_col", "cand_concept_radar", "cand_emotion_radar", "cand_mood_radar"], 'select' : {'rowsort': None}},
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'lines'   : {"liking.keyword" : {'0-Mean':['mean']}},
                "q-mean"  : True,
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                'sort'    : 'event',
                'legend'  : {'position': 'none'},
                "seriesType" : 'bars',
                "series"  : {1: {"type": 'line'}}
                },
            },
        } 


    dashboard_fresh_layout = OrderedDict()
    dashboard_fresh_layout['rows'] = [["emotion_ans_col"],["suitable_stage_ans_col", "suitable_product_ans_col"]]

    dashboard_fresh_hedonics = OrderedDict()
    dashboard_fresh_hedonics['rows'] = [["liking_blindcode_col"],["freshness_blindcode_col"], ["cleanliness_blindcode_col"]]

    dashboard_fresh_topline = OrderedDict()
    dashboard_fresh_topline['rows'] = [["topline_liking_table"],["topline_freshness_table"],["cand_emotion_col"]]

    dashboard_fresh_profile = OrderedDict()
    dashboard_fresh_profile['columns'] = [["topline_liking_table"],["cand_concept_radar", "cand_emotion_radar"],["cand_mood_radar"]]


    storyboard_fresh = [
        {'name'     : "Topline",
         'layout'   : dashboard_fresh_topline,
         #'active'   : True,
        },
        {'name'     : "Hedonics / Candidates",
         'layout'   : dashboard_fresh_hedonics,
         #'active'   : False,
        },
        {'name'     : "Profile",
         'layout'   : dashboard_fresh_profile,
         #'active'   : False,
        },
        {'name'     : "Questions / Answers",
         'layout'   : dashboard_fresh_layout,
         #'active'   : False,
        },
        #{'name'     : "Candidates / Hedonics",
        # 'layout'   : dashboard_candidates,
        # 'active'   : True,
        #},
        ]

    dashboard_link = {
        'liking_blindcode_col'      : dashboard_fresh['liking_blindcode_col'],
        'topline_liking_table'      : dashboard_fresh['topline_liking_table'],
        'freshness_blindcode_col'   : dashboard_fresh['freshness_blindcode_col'],
        'topline_freshness_table'   : dashboard_fresh['topline_freshness_table'],
        "cand_liking_col" : {
            'chart_type': "ComboChart",
            'chart_title' : "Liking Candidates #",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('!', [0,'','0']), {'a-wmean' : '**', 'q-mean' : '*'}],
                'order'   : { "_key" : "asc" },
                },
            'options'     : {
                "seriesType" : 'bars',
                "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
                },
            },
        "liking_blindcode_perc_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking Candidate %",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('!', [0,'','0']), {'a-mean' : '+'}],
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"},
            'options'     : {
                'sort'    : 'event',
                'frozenColumns' : 2,
                }
            },
        "topline_liking_perc_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate %",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_perc_col",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_emotion_col", "cand_concept_radar", "cand_emotion_radar", "cand_mood_radar"], 'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'answers' : [('!', [0,'','0'])],
                'calc'    : 'percentile',
                'lines'   : {"liking.keyword" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'Z_facet'     : {
                'field'   : "product_form.keyword",
                'label'   : "Product Form",
                'order'   : { "_key" : "asc" },
                'tiles'   : 'grid-2x1',
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                #'NumberFormat' : {1 : {'pattern' : '#.##'},2 : {'pattern' : '#.#'}},
                #'setColumnProperties'   : {1 : {'style': 'font-style:bold; font-size:22px;'}},
                'setProperty'   : [],
                #'setProperty'   : [[2, 1, 'style', 'font-style:bold;'],
                #                   [3, 3, 'background-color', 'red' ],
                #                   [0, 1, 'className', 'benchmark'],
                #                   [1, 1, 'className', 'benchmark'],
                #                   [2, 1, 'className', 'benchmark'],
                #                   [3, 1, 'className', 'benchmark'],
                #                   [4, 1, 'className', 'benchmark'],
                #                   ],
                },
            },
        "emotion_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Emotion %",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "emotion",
                'label'   : "Emotion",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'total'   : False },
            },
        "liking_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Liking %",
            'data_type'  : "facet",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Legend for sorting Categories",
            'listener'    : {'select' : {'colsort': 'categories'}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking with Mean ",
                #'answers' : [('=', '*'), ('!', [0,'','0']), {'a-mean' : '*'}, {'q-mean' : '+'}],
                'answers' : [('!', [0,'','0']), {'a-mean' : '+'}],
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                },
            'Z_facet'     : {
                'field'   : "product_form.keyword",
                'label'   : "Product Form",
                'order'   : { "_key" : "asc" },
                'tiles'   : 'dropdown',
                },
            },
        "freshness_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Freshness %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Legend for sorting Categories",
            'listener'    : {'select' : {'colsort': 'categories'}},
            'X_facet'     : {
                'field'   : "freshness",
                'label'   : "Freshness with Mean ",
                'answers' : [('!', [0,'','0']), {'a-mean' : '+'}],
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                },
            'Z_facet'     : {
                'field'   : "product_form.keyword",
                'label'   : "Product Form",
                'order'   : { "_key" : "asc" },
                'tiles'   : 'dropdown',
                },
            },
        "liking_emotion_corr_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Liking / Emotion Correlation",
            'data_type'   : "correlation",
            'base'        : ["liking_perc_col", "emotion_perc_col", "freshness_perc_col"],
            'controls'    : ['CategoryFilter'],
            'facts'       : {'liking.keyword': {'fact' : 'hedonics', 'value_type' : 'ordinal', 'calc' : 'w-avg'},
                             'freshness': {'fact' : 'hedonics', 'value_type' : 'ordinal', 'calc' : 'w-avg'},
                             'emotion'       : {'fact' : 'emotion',  'value_type' : 'boolean', 'calc' : 'w-avg'}},
            'listener'    : {'select' : {'join': ["liking_emotion_scatterl"]}},
            'X_facet'     : {
                'field'   : 'liking.keyword',
                'stats'   : ['answer', 'liking.keyword', 'mean', 'std', 'min', 'max', '25%', '50%', '75%', 'count'],
                'label'   : {'category' : 'Question',
                             'answer':'Answer', 'liking.keyword': 'Liking', 'mean':'Mean', 'std':'Std', 'min':'Min', 'max':'Max', '25%':'25%', '50%':'50%', '75%': '75%',
                             'count':'Tiles'},
                },
            'Y_facet'     : {
                'field'   : 'emotion',
                'corrs'   : 'emotion',
                'label'   : "Emotion"
                },
            'options'     : {
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        "liking_emotion_scatter" : {
            'chart_type'  : "ScatterChart",
            'chart_title' : "Liking / Emotion",
            'data_type'   : "join",
            'base'        : ["liking_perc_col", "emotion_perc_col"],
            'X_facet'     : {
                'field'   : 'liking.keyword',
                'label'   : "Liking/Hedonics",
                },
            'Y_facet'     : {
                'field'   : 'emotion',
                'label'   : "Emotion"
                },
            },
        "country_map" : {
            'chart_type'  : "GeoChart",
            #'data_type'  : 'aggr',
            'data_type'   : 'facet',
            'chart_title' : "Country Resp Count",
            'listener'    : {'select' : {'select_event': 'country_sel'}},
            'X_facet'     : {
                'field'   : "country.keyword",
                'total'   : True,
                'label'   : "Country" },
            },
        }

    # Guide storyboards
    storyboard_link_filters = [
        {'name'     : "link_filters_globe",
         'layout'   : OrderedDict({'rows': [['country_map']]}),
        },
        ]
    storyboard_link = [
        {'name'     : 'Topline',
         'layout'   : {'rows' : [['liking_blindcode_col'], ['cand_liking_col'], ['liking_blindcode_perc_col'], ['topline_liking_table'], ['topline_liking_perc_table']]},
         #'active'   : False,
        },
        {'name'     : 'Hedonics',
         'layout'   : {'rows' : [['topline_liking_perc_table']]},
         #'active'   : False,
        },
        {'name'     : 'Intensity',
         'layout'   : {'rows' : [['freshness_blindcode_col'], ['topline_freshness_table']]},
         #'active'   : False,
        },
        {'name'     : 'Driver Liking',
         'layout'   : {'rows' : [['liking_perc_col', 'freshness_perc_col'], ['emotion_perc_col'], ['liking_emotion_corr_table', 'liking_emotion_scatter']]},
         #'active'   : False,
        },
        {'name'     : 'Fresh',
         'layout'   : {'rows' : [['freshness_perc_col']]},
         #'active'   : False,
        }
        ]

    dashboard_orange = {
        "liking_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            },
        "strength_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Strength Candidate #",
            'data_type'  : "aggr",
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            # USE TRANSPOSE SINCE THE REVERSE_NESTING ON AGGR DOESN'T WORK
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            'Y_facet'     : {
                'field'   : "hedonics",
                'question': "Strength",
                "answers" : ["strength"],
                "values"  : [],
                "a-mean"  : True,
                'label'   : "Strength",
                'order'   : { "_key" : "asc" },
                },
            },
        "topline_liking_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate #",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_col",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_affective_radar", "cand_behavioral_radar", "cand_ballot_radar", "cand_descriptors_radar"], 'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'lines'   : {"liking.keyword" : {'0-Mean':['mean'], '1-Excellent':[9], '2-Top2':[9,8], '3-Top3':[9,8,7], '4-Bottom3':[3,2,1],'5-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                #'NumberFormat' : {1 : {'pattern' : '#.##'},2 : {'pattern' : '#.#'}},
                #'setColumnProperties'   : {1 : {'style': 'font-style:bold; font-size:22px;'}},
                'setProperty'   : [],
                #'setProperty'   : [[2, 1, 'style', 'font-style:bold;'],
                #                   [3, 3, 'background-color', 'red' ],
                #                   [0, 1, 'className', 'benchmark'],
                #                   [1, 1, 'className', 'benchmark'],
                #                   [2, 1, 'className', 'benchmark'],
                #                   [3, 1, 'className', 'benchmark'],
                #                   [4, 1, 'className', 'benchmark'],
                #                   ],
                },
            },
        "cand_affective_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Affective",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "affective",
                'question': "Affective",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Affective"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_behavioral_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Behavioral",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "behavioral",
                'question': "Behavioral",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Behavioral"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_ballot_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Ballot",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ballot",
                'question': "Ballot",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Ballot"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_descriptors_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Descriptors",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors",
                'question': "Descriptors",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                "a-mean"  : True,
                'label'   : "Descriptors"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        }

    dashboard_orange_hedonics = OrderedDict()
    dashboard_orange_hedonics['rows'] = [["liking_blindcode_col"],["strength_blindcode_col"]]

    dashboard_orange_profile = OrderedDict()
    dashboard_orange_profile['columns'] = [
            ["topline_liking_table"],["cand_affective_radar", "cand_behavioral_radar"],
            ["cand_ballot_radar", "cand_descriptors_radar"]
        ]

    storyboard_orange = [
        {'name'     : "Hedonics",
         'layout'   : dashboard_orange_hedonics,
         #'active'   : True,
        },
        {'name'     : "Profile",
         'layout'   : dashboard_orange_profile,
         #'active'   : False,
        }
        ]

    dashboard_panels = {
        "attributes_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Attributes %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "attributes",
                'label'   : "Attributes",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "cand_attributes_word" : {
            'chart_type': "WordCloudChart",
            'chart_title' : "Attributes",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "attributes",
                'question': "Attributes",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Attributes"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_attributes_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Attributes",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "attributes",
                'question': "Attributes",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Attributes"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_attributes_table" : {
            'chart_type': "Table",
            'chart_title' : "Attributes",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "attributes",
                'question': "Attributes",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Attributes"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_attributes_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Attributes Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "attributes",
                'question': "Attributes",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Attributes"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_expected_benefits_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Expected Benefits",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "expected_benefits",
                'question': "Expected Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Expected Benefits"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_expected_benefits_table" : {
            'chart_type': "Table",
            'chart_title' : "Expected Benefits",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "expected_benefits",
                'question': "Expected Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Expected Benefits"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_expected_benefits_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Expected Benefits Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "expected_benefits",
                'question': "Expected Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Expected Benefits"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_ideal_benefits_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Ideal Benefits",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ideal_benefits",
                'question': "Ideal Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Ideal Benefits"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_ideal_benefits_table" : {
            'chart_type': "Table",
            'chart_title' : "Ideal Benefits",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ideal_benefits",
                'question': "Ideal Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Ideal Benefits"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_ideal_benefits_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Ideal Benefits Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ideal_benefits",
                'question': "Ideal Benefits",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Ideal Benefits"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_olfactive_attr_table" : {
            'chart_type': "Table",
            'chart_title' : "Olfactive Attr",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "olfactive_attr",
                'question': "Olfactive Attr",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Olfactive Attr"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_olfactive_attr_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Olfactive Attr Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "olfactive_attr",
                'question': "Olfactive Attr",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Olfactive Attr"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_platform_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Platform",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "platform",
                'question': "Platform",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Platform"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_platform_table" : {
            'chart_type': "Table",
            'chart_title' : "Platform",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "platform",
                'question': "Platform",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Platform"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_platform_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Platform Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "platform",
                'question': "Platform",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Platform"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_industry_table" : {
            'chart_type': "Table",
            'chart_title' : "Industry",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "industry",
                'question': "Industry",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Industry"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_industry_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Industry Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "industry",
                'question': "Industry",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Industry"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "platform_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Platform %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "platform",
                'label'   : "Platform",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "color_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Color %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "color",
                'label'   : "Color",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'total'   : False },
            },
        "country_map" : {
            'chart_type'  : "GeoChart",
            #'data_type'  : 'aggr',
            'data_type'   : 'facet',
            'chart_title' : "Country Resp Count",
            'listener'    : {'select' : {'select_event': 'panel_country_sel'}},
            'X_facet'     : {
                'field'   : "country.keyword",
                'total'   : True,
                'label'   : "Country",
                'order'   : { "_key" : "asc" },
                }
            },
        "expected_benefits_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Expected Benefits %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "expected_benefits",
                'label'   : "Expected Benefits",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "ideal_benefits_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Ideal Benefits %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "ideal_benefits",
                'label'   : "Ideal Benefits",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "newness_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Newness %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "newness",
                'label'   : "Newness",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'total'   : False },
            },
        "intensity_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Intensity %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "hedonics",
                'label'   : "Intensity",
                'calc'    : 'percentile',
                "answers" : ['strength'],
                "values"  : [{'layout': 'categories'}],
                'order'   : { "_key" : "asc" },
                'total'   : False },
            },
        "liking_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Liking %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking",
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                'total'   : False },
            },
        "olfactive_attr_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Olfactive Attr %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "olfactive_attr",
                'label'   : "Olfactive Attr",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "cand_olfactive_attr_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Olfactive Attr",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "olfactive_attr",
                'question': "Olfactive Attr",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Olfactive Attr"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "liking_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('=', '*'), ('!', [0,'','0'])],
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            },
        "strength_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Strength Candidate #",
            'data_type'  : "aggr",
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            # USE TRANSPOSE SINCE THE REVERSE_NESTING ON AGGR DOESN'T WORK
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            'Y_facet'     : {
                'field'   : "hedonics",
                'question': "Strength",
                "answers" : ["strength"],
                "values"  : [],
                "a-mean"  : True,
                'label'   : "Strength",
                'order'   : { "_key" : "asc" },
                },
            },
        "topline_liking_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate #",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_col",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_attributes_radar", "cand_expected_benefits_radar", "cand_ideal_benefits_radar", "cand_olfactive_attr_radar", "cand_platform_radar"],
                             'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'lines'   : {"liking.keyword" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        "topline_strength_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Strength - Candidate #",
            'data_type'   : "aggr",
            #'base'        : "strength_blindcode_col",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_attributes_radar", "cand_expected_benefits_radar", "cand_ideal_benefits_radar", "cand_olfactive_attr_radar"], 'select' : {'rowsort': None}},
            'transpose'   : False,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            'Y_facet'     : {
                'field'   : "hedonics",
                'question': "Strength",
                "answers" : ["strength"],
                "values"  : [],
                "a-mean"  : True,
                'label'   : "Strength",
                'order'   : { "_key" : "asc" },
                },
            'result'      : {
                'lines'   : OrderedDict([('0-Mean',['mean']), ('1-JAR',[3]), ('2-Weak',[1,2]), ('3-Strong',[4,5])]),
                'transpose': True
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        "ttest_table" : {
            'chart_type'  : "Table",
            'chart_title' : "t-test Liking - Candidate",
            'data_type'   : "card_ttest",
            'controls'    : ['CategoryFilter'],
            "significance": 0.2, # 0.2 = 80%
            "test_type"   : "two-tailed",
            'X_facet'     : {
                'field'   : "blindcode",
                'label'   : "Candidate"
                },
            'Y_facet'     : {
                'field'   : "liking",
                'stats'   : ['answer', 'liking', 'count', 'mean', 'std', ],
                'label'   : {'category' : 'Question',
                             'answer':'Answer', 'liking.keyword': 'Liking', 'count':'Tiles', 'mean':'Mean', 'std':'Std'},
                },
            'options'     : {
                'sort'    : 'event',
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        }


    # Guide Storyboards
    storyboard_panels_filters = [
        {'name'     : "panel_filters_globe",
         'layout'   : OrderedDict({'rows': [['country_map']]}),
        },
        ]

    storyboard_panels_onepager = [
        {'name'     : "panel_onepager",
         'layout'   : OrderedDict({'rows': [["topline_liking_table"], ["topline_strength_table"],
                                            ["cand_attributes_top_table", "cand_olfactive_attr_top_table"],
                                            ["cand_expected_benefits_top_table", "cand_ideal_benefits_top_table"]]}),
        },
        {'name'     : "panel_onepager_ttest",
         'layout'   : OrderedDict({'rows': [["ttest_table"]]}),
        },
        ]
    storyboard_panels_liking = [
        {'name'     : "panel_liking_perc",
         'layout'   : OrderedDict({'rows': [["liking_perc_col", "intensity_perc_col"]]}),
        },
        {'name'     : "panel_liking_count",
         'layout'   : OrderedDict({'rows': [["liking_blindcode_col", "strength_blindcode_col"]]}),
        },
        {'name'     : "panel_topline",
         'layout'   : OrderedDict({'rows': [["topline_liking_table"]]}),
        },
        ]

    storyboard_panels_profile = [
        {'name'     : "panel_profile_emotion",
         'layout'   : OrderedDict({'rows': [["topline_liking_table"], ["cand_attributes_radar", "cand_platform_radar"],["cand_attributes_word"]]}),
        },
        {'name'     : "panel_profile_benefits",
         'layout'   : OrderedDict({'rows': [["topline_liking_table"], ["cand_expected_benefits_radar", "cand_ideal_benefits_radar"]]}),
        },
        {'name'     : "panel_profile_olfactive_attr",
         'layout'   : OrderedDict({'rows': [["topline_liking_table"], ["cand_olfactive_attr_radar"]]}),
        },
        ]

    storyboard_panels_topic = [
        {'name'     : "panel_topic_hedonics",
         'layout'   : OrderedDict({'rows': [["liking_perc_col", "intensity_perc_col"],
                                            ["liking_blindcode_col", "strength_blindcode_col"]]}),
        },
        {'name'     : "panel_topic_attributes",
         'layout'   : OrderedDict({'rows': [["attributes_perc_col"],
                                            ["cand_attributes_table", "cand_attributes_top_table"]]}),
        },
        {'name'     : "panel_topic_platform",
         'layout'   : OrderedDict({'rows': [["platform_perc_col"],
                                            ["cand_platform_table", "cand_platform_top_table"]]}),
        },
        {'name'     : "panel_topic_benefits",
         'layout'   : OrderedDict({'rows': [["expected_benefits_perc_col", "ideal_benefits_perc_col"]]}),
        },
        {'name'     : "panel_topic_olfactive_attr",
         'layout'   : OrderedDict({'rows': [["olfactive_attr_perc_col"],
                                            ["cand_olfactive_attr_table", "cand_olfactive_attr_top_table"]]}),
        },
        {'name'     : "panel_topic_color",
         'layout'   : OrderedDict({'rows': [["color_perc_col"]]}),
        },
        {'name'     : "panel_topic_newness",
         'layout'   : OrderedDict({'rows': [["olfactive_attr_perc_col", "newness_perc_col"]]}),
        },
        ]

    storyboard_panels_stats = [
        {'name'     : "panel_stats_emotion",
         'layout'   : OrderedDict({'rows': [["cand_attributes_table", "cand_attributes_top_table"],
                                            ["cand_platform_table", "cand_platform_top_table"]]}),
        },
        {'name'     : "panel_stats_benefits",
         'layout'   : OrderedDict({'rows': [["cand_expected_benefits_table", "cand_expected_benefits_top_table"],
                                            ["cand_ideal_benefits_table", "cand_ideal_benefits_top_table"]]}),
        },
        {'name'     : "panel_stats_olfactive_attr",
         'layout'   : OrderedDict({'rows': [["cand_olfactive_attr_table", "cand_olfactive_attr_top_table"],
                                            ["cand_industry_table", "cand_industry_top_table"]]}),
        },
        ]

    # Seeker Storyboard
    dashboard_panels_hedonics = OrderedDict()
    dashboard_panels_hedonics['rows'] = [["liking_perc_col", "intensity_perc_col"],
                                         ["liking_blindcode_col", "strength_blindcode_col"],
                                         ["topline_liking_table"]]
    dashboard_panels_topic = OrderedDict()
    dashboard_panels_topic['rows'] = [["attributes_perc_col", "platform_perc_col"],
                                      ["expected_benefits_perc_col", "ideal_benefits_perc_col"],
                                      ["olfactive_attr_perc_col", "newness_perc_col"]]
    dashboard_panels_stats = OrderedDict()
    dashboard_panels_stats['rows'] = [["ttest_table"]]
    dashboard_panels_profile = OrderedDict()
    dashboard_panels_profile['rows'] = [["topline_liking_table"], ["cand_attributes_radar", "cand_olfactive_attr_radar"]]

    storyboard_panels = [
        {'name'     : "Hedonics",
         'layout'   : dashboard_panels_hedonics,
        },
        {'name'     : "Topic",
         'layout'   : dashboard_panels_topic,
        },
        {'name'     : "Stats",
         'layout'   : dashboard_panels_stats,
        },
        {'name'     : "Profile",
         'layout'   : dashboard_panels_profile,
        },
        ]

    dashboard_invictus = {
        "descriptors1_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Descriptors 1 %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "descriptors1",
                'label'   : "Descriptors1",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "cand_descriptors1_word" : {
            'chart_type': "WordCloudChart",
            'chart_title' : "Descriptors1",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors1",
                'question': "Descriptors1",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Descriptors1"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_descriptors1_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Descriptors1",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors1",
                'question': "Descriptors1",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Descriptors1"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "cand_descriptors1_table" : {
            'chart_type': "Table",
            'chart_title' : "Descriptors1",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors1",
                'question': "Descriptors1",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Descriptors1"
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "cand_descriptors1_top_table" : {
            'chart_type': "Table",
            'chart_title' : "Descriptors1 Top-3",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : False,
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors1",
                'question': "Descriptors1",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Descriptors1"
                },
            'result'      : {
                'top'     : 3
                },
            'options'     : {
                #'sort'    : 'event',
                'frozenColumns' : 2, # will be adjusted by bind_aggr
                },
            },
        "descriptors2_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Descriptors2 %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "descriptors2",
                'label'   : "Descriptors2",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "cand_descriptors2_radar" : {
            'chart_type': "RadarChart",
            'chart_title' : "Descriptors2",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "descriptors2",
                'question': "Descriptors2",
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'label'   : "Descriptors 2"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "descriptors3_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Descriptors3 %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "descriptors3",
                'label'   : "Descriptors3",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "descriptors4_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Descriptors4 %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "descriptors4",
                'label'   : "Descriptors4",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "color_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Color %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "color",
                'label'   : "Color",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'total'   : False },
            },
        "imagine_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Imagine %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "imagine",
                'label'   : "Imagine",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "fit_descriptors1_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Fit Descriptors1 %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "fit_descriptors1",
                'label'   : "Fit Descriptors1",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes"],
                'total'   : False },
            },
        "country_map" : {
            'chart_type'  : "GeoChart",
            #'data_type'  : 'aggr',
            'data_type'   : 'facet',
            'chart_title' : "Country Resp Count",
            'listener'    : {'select' : {'select_event': 'panel_country_sel'}},
            'X_facet'     : {
                'field'   : "country.keyword",
                'total'   : True,
                'label'   : "Country",
                'order'   : { "_key" : "asc" },
                }
            },
        "intensity_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Intensity %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "intensity",
                'label'   : "Intensity",
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                'total'   : False },
            },
        "liking_perc_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Liking %",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'listener'    : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking",
                'calc'    : 'percentile',
                'order'   : { "_key" : "asc" },
                'total'   : False },
            },
        "liking_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking Candidate #",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('=', '*'), ('!', [0,'','0'])],
                'order'   : { "_key" : "asc" },
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            },
        "intensity_blindcode_col" : {
            'chart_type': "Table",
            'chart_title' : "Strength Candidate #",
            'data_type'  : "aggr",
            'transpose'   : True,
            'listener'    : {'select' : {'rowsort': None}},
            # USE TRANSPOSE SINCE THE REVERSE_NESTING ON AGGR DOESN'T WORK
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            'Y_facet'     : {
                'field'   : "intensity",
                'label'   : "Intensity",
                'answers' : [('=', '*'), ('!', [0,'','0'])],
                'order'   : { "_key" : "asc" },
                },
            },
        "topline_liking_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Liking - Candidate #",
            'data_type'   : "aggr",
            'base'        : "liking_blindcode_col",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_descriptors1_radar", "cand_descriptors1_radar", "cand_descriptors3_radar", "cand_descriptors4_radar", "cand_fit_descriptors1_radar"],
                             'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Hedonics_",
                'lines'   : {"liking.keyword" : {'0-Mean':['mean'], '1-Excellent':[7], '2-Top2':[7,6], '3-Bottom2':[2,1]}},
                },
            'Y_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        "topline_strength_table" : {
            'chart_type'  : "Table",
            'chart_title' : "Topline Strength - Candidate #",
            'data_type'   : "aggr",
            #'base'        : "strength_blindcode_col",
            'controls'    : ['CategoryFilter', 'tile_layout_select'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'sort' : ["cand_descriptors1_radar", "cand_descriptors1_radar", "cand_descriptors3_radar", "cand_descriptors4_radar", "cand_fit_descriptors1_radar"],
                             'select' : {'rowsort': None}},
            'transpose'   : False,
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate" },
            'Y_facet'     : {
                'field'   : "hedonics",
                'question': "Strength",
                "answers" : ["strength"],
                "values"  : [],
                "a-mean"  : True,
                'label'   : "Strength",
                'order'   : { "_key" : "asc" },
                },
            'result'      : {
                'lines'   : OrderedDict([('0-Mean',['mean']), ('1-JAR',[3]), ('2-Weak',[1,2]), ('3-Strong',[4,5])]),
                'transpose': True
                },
            'options'     : {
                'sort'    : 'event',
                "allowHtml" : True,
                'frozenColumns' : 2,
                },
            'formatter'  : {
                'setProperty'   : [],
                },
            },
        }

    # Seeker Storyboard
    dashboard_invictus_hedonics = OrderedDict()
    dashboard_invictus_hedonics['rows'] = [["liking_perc_col", "intensity_perc_col"],
                                         ["liking_blindcode_col", "intensity_blindcode_col"],
                                         ["topline_liking_table"]]
    dashboard_invictus_topic = OrderedDict()
    dashboard_invictus_topic['rows'] = [["descriptors1_perc_col", "descriptors2_perc_col"],
                                      ["descriptors3_perc_col", "descriptors4_perc_col"],
                                      ["color_perc_col", "fit_descriptors1_perc_col"],
                                      ["imagine_perc_col"]]
    dashboard_invictus_profile = OrderedDict()
    dashboard_invictus_profile['rows'] = [["topline_liking_table"], ["cand_descriptors1_radar", "cand_descriptors2_radar"]]

    storyboard_invictus = [
        {'name'     : "Hedonics",
         'layout'   : dashboard_invictus_hedonics,
        },
        {'name'     : "Topic",
         'layout'   : dashboard_invictus_topic,
        },
        {'name'     : "Profile",
         'layout'   : dashboard_invictus_profile,
        },
        ]

    workbooks = {
        "fresh and clean" : {
            'display'       : ["gender", "age", 'brand', "blindcode", "freshness"],
            'facets'        : ["survey.keyword", "country.keyword", "gender.keyword", "age.keyword", "cluster.keyword", "brand.keyword", "product_form.keyword",
                               "method.keyword", "blindcode.keyword", "olfactive.keyword", "perception.keyword", "liking.keyword"],
            'tiles'         : ["country.keyword", "gender.keyword", "age.keyword", "product_form.keyword", "method.keyword", "blindcode.keyword"],
            'charts'        : dashboard_fresh,
            'storyboards'   : {'initial' : storyboard_fresh},
            'dashboard_data': 'pull',
            'filters'       : {'survey.keyword' : ["fresh and clean"]}
            },
        "link" : {
            'display'       : ["gender", "age", 'brand', "blindcode", "freshness"],
            'facets'        : ["survey.keyword", "country.keyword", "gender.keyword", "age.keyword", "cluster.keyword", "brand.keyword", "product_form.keyword",
                               "method.keyword", "blindcode.keyword", "olfactive.keyword", "perception.keyword", "liking.keyword"],
            'tiles'         : ["country.keyword", "gender.keyword", "age.keyword", "product_form.keyword", "method.keyword", "blindcode.keyword"],
            'charts'        : dashboard_link,
            'storyboards'   : {'initial' : storyboard_link,
                               'link_filters': storyboard_link_filters},
            'dashboard_data': 'pull',
            'filters'       : {'survey.keyword' : ["fresh and clean"]},
            'qst2fld'       : {},
            },
        "orange beverages" : {
            'display'       : ["gender", "age", 'brand', "blindcode", "liking"],
            'facets'        : ["survey.keyword", "gender.keyword", "age.keyword", "blindcode.keyword", "liking.keyword",
                               "hedonics", "affective", "ballot", "behavioral", "physical"],
            'tiles'         : ["gender.keyword", "age.keyword", "blindcode.keyword"],
            'charts'        : dashboard_orange,
            'storyboards'   : {'initial' : storyboard_orange},
            'dashboard_data': 'push',
            'filters'       : {'survey.keyword' : ["orange beverages"]},
            'qst2fld'       : {},
            },
        "global panels" : {
            'display'       : ["gender", "age", 'brand', "blindcode", "freshness"],
            'facets'        : ["survey.keyword", "category.cat.keyword", "country.keyword", "gender.keyword", "age.keyword", "brand.keyword", "product_form.keyword",
                               "method.keyword", "blindcode.keyword", "liking.keyword"],
            'tiles'         : ["country.keyword", "gender.keyword", "age.keyword", "product_form.keyword", "method.keyword", "blindcode.keyword"],
            'charts'        : dashboard_panels,
            'storyboards'   : {'initial' : storyboard_panels,
                               'panel_filters': storyboard_panels_filters,
                               'panel_onepager' : storyboard_panels_onepager,
                               'panel_liking' : storyboard_panels_liking,
                               'panel_profile' : storyboard_panels_profile,
                               'panel_topic' : storyboard_panels_topic,
                               'panel_stats' : storyboard_panels_stats,},
            'dashboard_data': 'pull',
            'filters'       : {'survey.keyword' : ["global panels"]},
             #'qst2fld'       : survey.surveys["global panels"]['questions'],
            'qst2fld'       : {
                "attributes"        : (["attributes"], 'nested_qst_ans'),
                "platform"          : (["platform"], 'nested_qst_ans'),
                "color"             : (["color"], 'nested_qst_ans'),
                "consumer_nature"   : (["consumer_nature"], 'nested_qst_ans'),
                "expected_benefits" : (["expected_benefits"], 'nested_qst_ans'),
                "health_condition"  : (["health_condition"], 'nested_qst_ans'),
                "ideal_benefits"    : (["ideal_benefits"], 'nested_qst_ans'),
                "industry"          : (["industry"], 'nested_qst_ans'),
                "format_rejected"   : (["format_rejected"], 'nested_qst_ans'),
                "format_used"       : (["format_used"], 'nested_qst_ans'),
                "newness"           : (["newness"], 'nested_qst_ans'),
                "product"           : (["product"], 'nested_qst_ans'),
                "purpose"           : (["purpose"], 'nested_qst_ans'),
                "olfactive_attr"    : (["olfactive_attr"], 'nested_qst_ans'),
                    }
            },
        "invictus ul" : {
            'display'       : ["group_id", "age", 'country', "blindcode", "liking"],
            'facets'        : ["survey.keyword", "category.cat.keyword", "country.keyword", "age.keyword",
                               "group_id.keyword", "blindcode.keyword", "liking.keyword"],
            'tiles'         : ["country.keyword", "age.keyword", "group_id.keyword", "blindcode.keyword"],
            'charts'        : dashboard_invictus,
            'storyboards'   : {'initial' : storyboard_invictus},
            'dashboard_data': 'pull',
            'filters'       : {'survey.keyword' : ["invictus ul"]},
            'qst2fld'       : {
                "descriptors1"      : (["descriptors1"], 'nested_qst_ans'),
                "descriptors2"      : (["descriptors2"], 'nested_qst_ans'),
                "descriptors3"      : (["descriptors3"], 'nested_qst_ans'),
                "color"             : (["color"], 'nested_qst_ans'),
                "descriptors4"      : (["descriptors4"], 'nested_qst_ans'),
                "imagine"           : (["imagine"], 'nested_qst_ans'),
                "fit_descriptors1"  : (["fit_descriptors1"], 'nested_qst_ans'),
                    }
            },
    }

    ### GLOBAL VARIABLES
             
scrape_li = []
posts_df = DataFrame()
search_keywords = {}
molecules_d = {}

scrape_q = queue.Queue()



