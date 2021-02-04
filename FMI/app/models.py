"""
Definition of models.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.contrib.auth.models import AbstractUser

# Create your models here.
import queue
import collections
from collections import OrderedDict
import datetime
import FMI.settings
from pandas import DataFrame

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl import Date, Boolean, Text, Nested, Keyword
from elasticsearch_dsl.connections import connections
import seeker

import app.wb_excel as wb_excel


client = Elasticsearch(FMI.settings.ES_HOSTS)


import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'es_index_name', 'es_type_name', 'es_mapping'
)

###
### Workbooks, need to migrate to wb_excel
###

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

###
### Excel
###

class ExcelSeekerView (seeker.SeekerView):
    site = FMI.settings.site
    document = None
    using = client
    index = "excel"
    page_size = 30
    facets = [
        ]
    facets_keyword = [];
    display = [
        ]
    sort = []
    summary = []
    sumheader = []
    SUMMARY_URL="{}"
    urlfields = {
        }
    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}


class Review(models.Model):
    reviewid = models.IntegerField()
    site = models.TextField()
    brand_name = models.TextField()
    brand_variant = models.TextField()
    perfume = models.TextField()
    review_date = models.DateField()
    review = models.TextField()
    label = models.TextField()
    accords = []
    notespyramid = {}
    moods = []
    notes = []
    longevity = []
    sillage = []
    ratings = []
    img_src = models.TextField()

    class Meta:
        es_index_name = 'review'
        es_type_name = 'perfume'
        es_mapping = {
            'properties' : {
                'site'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'brand'          : {
                    'properties' : {
                        'name'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'variant'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'perfume'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'review_date'   : {'type' : 'date'},
                'review'        : {'type' : 'text'},
                'label'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'accords'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'notespyramid' :  {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'moods'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'notes'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'longevity'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'sillage'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'ratings'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'img_src'        : {'type' : 'text'},
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.reviewid
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_brand(self):
        return {'name': self.brand_name, 'variant': self.brand_variant}
    def get_es_accords(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.accords.items()]
    def get_es_moods(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.moods.items()]
    def get_es_notes(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.notes.items()]
    def get_es_longevity(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.longevity.items()]
    def get_es_sillage(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.sillage.items()]
    def get_es_ratings(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.ratings.items()]


class PerfumeSeekerView (seeker.SeekerView):
    site = FMI.settings.site
    document = None
    using = client
    index = "review"
    page_size = 30
    extra_columns = {"moods2" : {'field': 'moods', 'nestedfield': 'moods'}}
    field_column_types = {'moods2': 'JavaScriptColumn'}
    facets = [
        seeker.TermsFacet("site.keyword", label = "Site"),
        seeker.TermsFacet("brand.name.keyword", label = "Brand"),
        seeker.TermsFacet("perfume.keyword", label = "Perfume"),
        #seeker.YearHistogram("review_date", label = "Reviewed"),
        seeker.MonthHistogram("review_date", label = "Reviewed"),
        seeker.TermsFacet("label.keyword", label = "Sentiment"),
        seeker.TermsFacet("notespyramid.keyword", label = "Top Notes Pyramid"),
        seeker.PercFacet("accords.val.keyword", label = "Accords", nestedfield="accords"),
        seeker.PercFacet("moods.val.keyword", label = "Moods", nestedfield="moods"),
        seeker.PercFacet("notes.val.keyword", label = "Notes", nestedfield="notes"),
        seeker.PercFacet("longevity.val.keyword", label = "Longevity", nestedfield="longevity", visible_pos=0),
        seeker.PercFacet("sillage.val.keyword", label = "Sillage", nestedfield="sillage", visible_pos=0),
        seeker.PercFacet("ratings.val.keyword", label = "Ratings", nestedfield="ratings", visible_pos=0),
        ]
    facets_keyword = [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")];
    display = [
        "perfume",
        "review_date",
        "img_src",
        "site",
        "review",
        "label",
        "accords",
        "moods"
        ]
    field_labels = {
        "notespyramid"  : "Top Notes",
        "moods2"        : "Moods Bar Chart"
        }
    sort = [
        "-review_date"
        ]
    summary = ['review']
    sumheader = ['perfume']
    urlfields = {
        "perfume" : ""
        }
    SUMMARY_URL="fragrantica"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    minicharts = {
        'moods2' : {
            'chart_type'  : "ColumnChart",
            'chart_title' : "Moods %",
            'data_type'   : "nestedfield",
            'controls'    : [],
            #'listener'   : {'select' : {'colsort': None}},
            'X_facet'     : {
                'field'   : "moods",
                "answers" : [],
                'total'   : False,
                'label'   : "Moods" },
            'Z_facet'     : {
                'tiles'   : 'minichart',
                },
            'options'     : {
                'legend'  :'none',
                'width'   : 200,
                'height'  : 150},
            }
        }

    dashboard = {
        'perfume_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Perfume / Keyword Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "perfume.keyword",
                'label'   : "Perfume" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_label_table" : {
            'chart_type': "Table",
            'chart_title' : "Keyword / Category Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'Y_facet'     : {
                'field'   : "label.keyword",
                'label'   : "Label" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "reviewed_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Reviewed Year-Month Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "review_date",
                'label'   : "Reviewed",
                'key'     : 'key_as_string',
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM'},
                },
            },
        "cand_moods_like_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Moods-Like Perfumes",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'select' : {'colsort': None, 'rowcolfilter': ["accords_cand_radar", "moods_cand_radar", "notes_cand_radar",
                                                                           "longevity_cand_radar", "sillage_cand_radar", "ratings_cand_radar"]}},
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "moods",
                'question': "moods",
                "answers" : ['like'], # All
                "metric"  : "prc",
                #"a-mean"  : True,
                'label'   : "Moods-Like",
                }
            },
        "accords_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Accords",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "accords",
                'question': "accords",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Accords"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "moods_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Moods",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "moods",
                'question': "moods",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Moods"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "notes_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Notes",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "notes",
                'question': "notes",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Notes"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "longevity_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Longevity",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "longevity",
                'question': "longevity",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Longevity"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "sillage_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Sillage",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "sillage",
                'question': "sillage",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Sillage"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "ratings_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Ratings",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ratings",
                'question': "ratings",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Ratings"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        }

    dashboard_layout = collections.OrderedDict()
    dashboard_layout['table1'] = [["reviewed_keyword_line"], ["keyword_label_table"]]
    dashboard_layout['table2'] = [["perfume_keyword_table", "keyword_pie"]]

    dashboard_profile = collections.OrderedDict()
    dashboard_profile['table1'] = [["cand_moods_like_col"],
                                   ["accords_cand_radar", "moods_cand_radar"],
                                   ["longevity_cand_radar", "sillage_cand_radar"],
                                   ["notes_cand_radar", "ratings_cand_radar"],
                                   ]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         },
        {'name' : 'profile',
         'layout'   : dashboard_profile,
         }
    ]


###
### Market Intelligence
###

#class PostDoc(seeker.ModelIndex):
# done by models.PostDoc = seeker.mapping.document_from_model(models.Post, index="post", using=models.client)
class PostMap(models.Model):
    post_id = models.IntegerField()
    editor_id = models.CharField(max_length=30)
    published_date = models.DateField()
    post_category_id = models.CharField(max_length=30)
    title = models.CharField(max_length=256)
    relevance = models.TextField()
    subject = models.TextField()
    topline = models.TextField()
    source = models.TextField()
    article = models.TextField()
    average_rating = models.FloatField()
    rating_count = models.IntegerField()
    num_comments_id = models.IntegerField()
    class Meta:
        es_index_name = 'post'
        es_type_name = 'post'
        es_mapping = {
            'properties' : {
                'editor_id'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'published_date'    : {'type' : 'date'},
                'post_category_id'  : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'             : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'relevance'         : {'type' : 'text'},
                'subject'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'topline'           : {'type' : 'text'},
                'source'            : {'type' : 'text'},
                'article'           : {'type' : 'text'},
                'average_rating'    : {'type' : 'float'},
                'rating_count'      : {'type' : 'integer', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'num_comments_id'   : {'type' : 'integer', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_article(self, field_name):
        list_es_value = getattr(self, field_name)
        if len(list_es_value) > 32766:
            list_es_value = list_es_value[:32766]
        return list_es_value


class PostSeekerView (seeker.SeekerView, PostWorkbook):
    site = FMI.settings.site
    document = None
    using = client
    index = "post"
    page_size = 30
    facets = [
        seeker.TermsFacet("post_category_id.keyword", label = "Category"),
        seeker.TermsFacet("editor_id.keyword", label = "Editor"),
        seeker.TermsFacet("subject.keyword", label = "Subject"),
        #seeker.YearHistogram("published_date", label = "Published Year"),
        seeker.MonthHistogram("published_date", label = "Published Month"),
        #seeker.RangeFilter("rating_count", label = "Rating"),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "post_category_id",
        "published_date",
        "title",
        "subject",
        "relevance",
        "topline"
        ]
    summary = [
        "article"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="https://iffconnect.iff.com/Fragrances/marketintelligence/Lists/Posts/ViewPost.aspx?ID={}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}


###
### Costmetics
###

class PageMap(models.Model):
    page_id = models.IntegerField()
    published_date = models.DateField()
    site = models.TextField()
    sub_site = models.TextField()
    section = models.TextField()
    title = models.TextField()
    url = models.TextField()
    img_src = models.TextField()
    page = models.TextField()

    class Meta:
        es_index_name = 'page'
        es_type_name = 'page'
        es_mapping = {
            'properties' : {
                'published_date': {'type' : 'date'},
                'site'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'sub_site'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'section'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'         : {'type' : 'text'},
                'url'           : {'type' : 'text'},
                'img_src'       : {'type' : 'text'},
                'page'          : {'type' : 'text'},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.page_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value


class PageSeekerView (seeker.SeekerView, PageWorkbook):
    site = FMI.settings.site
    document = None
    using = client
    index = "page"
    page_size = 30
    facets = [
        seeker.TermsFacet("site.keyword", label = "Site"),
        seeker.TermsFacet("sub_site.keyword", label = "Sub Site"),
        seeker.TermsFacet("section.keyword", label = "Section"),
        seeker.MonthHistogram("published_date", label = "Published Month"),
        seeker.YearHistogram("published_date", label = "Published Year")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "published_date",
        "title",
        "site",
        "sub_site",
        ]
    summary = [
        "page"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="{}"


    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = collections.OrderedDict()
    dashboard_layout = {}
    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ] 

###
### FEEDLY
###

class FeedlyMap(models.Model):
    post_id = models.IntegerField()
    subset = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    feed = models.TextField()
    feed_topics = models.TextField()
    body_topics = models.TextField()
    title = models.TextField()
    url = models.TextField()
    body = models.TextField()

    class Meta:
        es_index_name = 'feedly'
        es_type_name = 'feedly'
        es_mapping = {
            'properties' : {
                'published_date'    : {'type' : 'date'},
                'subset'            : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'category'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'feed'              : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'feed_topics'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'body_topics'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'             : {'type' : 'text'},
                'url'               : {'type' : 'text'},
                'body'              : {'type' : 'text'},
                #'body'              : {'type' : 'text', 'fields' : {
                #    'body_keepwords'    : {'type': 'text', 'analyzer': 'keepwords'},
                #    'body_keeplength'   : {'type': 'token_count', 'analyzer': 'keepwords'}}},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value


class FeedlySeekerView (seeker.SeekerView):
    site = FMI.settings.site
    document = None
    using = client
    index = "feedly"
    page_size = 30
    facets = [
        seeker.TermsFacet("subset.keyword", label = "Subset"),
        seeker.TermsFacet("category.keyword", label = "Category"),
        seeker.TermsFacet("feed.keyword", label = "Feed"),
        seeker.TermsFacet("feed_topics.keyword", label = "Topics"),
        seeker.DayHistogram("published_date", label = "Published")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "published_date",
        "title",
        "category",
        "feed",
        "feed_topics",
        "body_topics",
        ]
    summary = [
        "body"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="{}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = {
        'category_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Category / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "category.keyword",
                'label'   : "Category" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        'feed_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Feed / Keyword Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "feed.keyword",
                'label'   : "Feed" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "customer_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Customer Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_cust",
                'label'   : "Customer" },
            },
        "competitor_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Competitor Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_comp",
                'label'   : "Competitor" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Year Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'key'     : 'key_as_string',
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM/d'},
                },
            },
        }
    dashboard_layout = collections.OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"], ["customer_pie", "competitor_pie", "keyword_pie"]]
    dashboard_layout['rows2'] = [["category_keyword_table", "feed_keyword_table"]]
    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ]       

###
### MAIL
###

class MailMap(models.Model):
    post_id = models.IntegerField()
    to_addr = models.TextField()
    from_addr = models.TextField()
    published_date = models.DateField()
    subject = models.TextField()
    links = models.TextField()
    url = models.TextField()
    body = models.TextField()

    class Meta:
        es_index_name = 'mail'
        es_type_name = 'mail'
        es_mapping = {
            'properties' : {
                'to_addr'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'from_addr'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'published_date'    : {'type' : 'date'},
                'subject'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'body'              : {'type' : 'text'},
                'links'             : {
                                        'type'       : 'nested',
                                        'properties' : {
                                            'name' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                            'url'  : {'type' : 'text', 'index': 'false'},
                                            'body' : {'type' : 'text'},
                                            }
                    },
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_links(self, field_name):
        return [{'name': link[0], 'url': link[1], 'body': link[2]} for link in self.links]


class MailSeekerView (seeker.SeekerView):
    site = FMI.settings.site
    document = None
    using = client
    index = "mail"
    page_size = 30
    field_column_types = {'links': 'LinksColumn'}
    facets = [
        seeker.TermsFacet("to_addr.keyword", label = "To"),
        seeker.TermsFacet("from_addr.keyword", label = "From"),
        seeker.TermsFacet("subject.keyword", label = "Subject"),
        seeker.DayHistogram("published_date", label = "Published")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        ];
    display = [
        "published_date",
        "from_addr",
        "subject",
        "links"
        ]
    search_children = ['links.body']
    summary = [
        "body"
        ]
    sumheader = [
        "subject"
        ]
    urlfields = {
        "subject" : ""
        }
    SUMMARY_URL="{}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = {
        'from_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "From / Keyword Doc Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "from_addr.keyword",
                'label'   : "From" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Doc Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Year Doc Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'key'     : 'key_as_string',
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM/d'},
                },
            },
        }
    dashboard_layout = collections.OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"], ["from_keyword_table", "keyword_pie"]]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ]       


###
### Scent Emotion (CFT - Ingredients)
###

class ScentemotionMap(models.Model):
    cft_id = models.IntegerField()
    dataset = models.TextField()
    ingr_name = models.TextField()
    IPC = models.TextField()
    supplier = models.TextField()
    olfactive = models.TextField()
    region = models.TextField()
    review = models.TextField()
    dilution = models.TextField()
    intensity = models.TextField()
    mood = []
    smell = []
    negative = []
    descriptor = []
    color = []
    texture = []
    emotion = []
    hedonics = []

    class Meta:
        es_index_name = 'scentemotion'
        es_type_name = 'scentemotion'
        es_mapping = {
            "properties" : {
                "dataset"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "ingr_name"         : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                "IPC"               : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "supplier"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "olfactive"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "region"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "review"            : {"type" : "text"},
                "dilution"          : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                "intensity"         : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                'mood'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'smell'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'negative'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'descriptor'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'color'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'texture'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'emotion'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'hedonics'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.cft_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def get_es_mood(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_smell(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_negative(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_descriptor(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_color(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_texture(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_emotion(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_hedonics(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
                if config['type'] == 'integer' and type(field_es_value) == str:
                    field_es_value = int(float(field_es_value))
                if (config['type'] == 'string' or config['type'] == 'text') and type(field_es_value) == int:
                    field_es_value = "{0:d}".format(field_es_value)
        return field_es_value


class ScentemotionSeekerView (seeker.SeekerView, ScentemotionWorkbook):
    site = FMI.settings.site
    document = None
    using = client
    index = "scentemotion"
    page_size = 20
    facets = [
        seeker.TermsFacet("dataset.keyword", label = "Dataset / Survey"),
        seeker.TermsFacet("olfactive.keyword", label = "Olfactive"),
        seeker.TermsFacet("region.keyword", label = "Region"),
        seeker.TermsFacet("IPC.keyword", label = "IPC", visible_pos=0),
        seeker.TermsFacet("intensity", label = "Intensity", nestedfield="intensity", visible_pos=0),
        #seeker.TermsFacet("mood.keyword", label = "Mood"),
        #seeker.TermsFacet("smell.keyword", label = "Smell"),
        seeker.PercFacet("mood.val.keyword", label = "Mood", nestedfield="mood"),
        seeker.PercFacet("smell.val.keyword", label = "Smell", nestedfield="smell"),
        seeker.PercFacet("negative.val.keyword", label = "Negative", nestedfield="negative"),
        seeker.PercFacet("descriptor.val.keyword", label = "Descriptor", nestedfield="descriptor"),
        seeker.PercFacet("color.val.keyword", label = "Color", nestedfield="color"),
        seeker.PercFacet("texture.val.keyword", label = "Texture", nestedfield="texture"),
        seeker.PercFacet("emotion.val.keyword", label = "Emotion", nestedfield="emotion", visible_pos=0),
        seeker.PercFacet("hedonics.val.keyword", label = "Hedonics", nestedfield="hedonics", visible_pos=0),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Benchmark", input="keywords_k"),
        ];
    display = [
        "IPC",
        "ingr_name",
        "olfactive",
        'intensity',
        "descriptor",
        "region",
        "mood",
        "smell",
        "negative",
        "review",
        ]
    sort = [
        #"-descriptor"
    ]
    exclude = [
        "cft_id",
        "dataset",  
        ]
    field_labels = {
        "mood"        : "Mood",
        "smell"       : "Smell",
        "negative"    : "Negative",
        "descriptor"  : "Descr",
        "color"       : "Color",
        "texture"     : "Texture"
        }
    summary = [
        ]
    sumheader = ["ingr_name"]
    urlfields = {
        "IPC"       : "http://sappw1.iff.com:50200/irj/servlet/prt/portal/prtroot/com.sap.ip.bi.designstudio.nw.portal.ds?APPLICATION=E2ESCENARIO_002?{0}",
        "ingr_name" : "http://www.iff.com/smell/online-compendium#{0}"
        }
    SUMMARY_URL="http://www.iff.com/smell/online-compendium#amber-xtreme"

    tabs = {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'}
      
    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements

###
### Survey (CI)
###

class SurveyMap(models.Model):
    # Survey attributes
    survey = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    stage = models.TextField()
    # Respondent Attributes
    resp_id = models.TextField()
    group_id = models.TextField()
    country = models.TextField()
    gender = models.TextField()
    age = models.TextField()
    ethnics = models.TextField()
    city = models.TextField()
    regions = models.TextField()
    education = models.TextField()
    income = models.TextField()
    # Product attributes
    blindcode = models.TextField()
    cluster = models.TextField()
    brand = models.TextField()
    variant = models.TextField()
    # Questions
    olfactive = models.TextField()
    method = models.TextField()
    product_form = models.TextField()
    # Ordinal Questions
    perception = models.TextField()
    freshness = models.IntegerField()
    cleanliness = models.IntegerField()
    lastingness  = models.IntegerField()
    intensity = models.IntegerField()
    liking = models.TextField()
    # Binary Questions
    affective = []
    ballot = []
    behavioral = []
    children = []
    concept = []
    descriptors = []
    descriptors1 = []
    descriptors2 = []
    descriptors3 = []
    descriptors4 = []
    emotion = []
    fragrattr = []
    hedonics = []
    imagine = []
    mood = []
    physical = []
    smell = []
    suitable_product = []
    suitable_stage = []
    # Fit Questions
    fit_descriptors1 = []
    fit_descriptors2 = []
    fit_descriptors3 = []
    fit_descriptors4 = []

    class Meta:
        es_index_name = 'survey'
        es_type_name = 'survey'
        es_mapping = {
            "properties" : {
                "survey"            : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                'published_date'    : {'type' : 'date'},
                #"category"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                'category'          : {
                    'properties' : {
                        'cat' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'subcat'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                "stage"             : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "resp_id"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "group_id"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "country"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "cluster"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "gender"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "age"               : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "ethnics"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "city"              : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "regions"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "education"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "income"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "blindcode"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "brand"             : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "variant"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "olfactive"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "perception"        : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "method"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "product_form"      : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                'freshness'         : {'type' : 'integer'},
                'cleanliness'       : {'type' : 'integer'},
                'lastingness'       : {'type' : 'integer'},
                'intensity'         : {'type' : 'integer'},
                "liking"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},

                'affective'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'ballot'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'behavioral'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'children'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'concept'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors1'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors2'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors3'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors4'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'emotion'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fragrattr'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'hedonics'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'imagine'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'mood'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'physical'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'smell'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'suitable_product'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'suitable_stage'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors1'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors2'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors3'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors4'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.resp_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
                if config['type'] == 'integer' and type(field_es_value) == str:
                    field_es_value = int(float(field_es_value))
        return field_es_value
    def get_es_affective(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.affective.items()]
    def get_es_ballot(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.ballot.items()]
    def get_es_behavioral(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.behavioral.items()]
    def get_es_children(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.children.items()]
    def get_es_concept(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.concept.items()]
    def get_es_descriptors(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors.items()]
    def get_es_descriptors1(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors1.items()]
    def get_es_descriptors2(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors2.items()]
    def get_es_descriptors3(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors3.items()]
    def get_es_descriptors4(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors4.items()]
    def get_es_emotion(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.emotion.items()]
    def get_es_fragrattr(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fragrattr.items()]
    def get_es_hedonics(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.hedonics.items()]
    def get_es_imagine(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.imagine.items()]
    def get_es_mood(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.mood.items()]
    def get_es_physical(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.physical.items()]
    def get_es_smell(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.smell.items()]
    def get_es_suitable_product(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.suitable_product.items()]
    def get_es_suitable_stage(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.suitable_stage.items()]
    def get_es_fit_descriptors1(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors1.items()]
    def get_es_fit_descriptors2(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors2.items()]
    def get_es_fit_descriptors3(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors3.items()]
    def get_es_fit_descriptors4(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors4.items()]


class SurveySeekerView (seeker.SeekerView, SurveyWorkbook):
    site = FMI.settings.site
    document = None
    using = client
    index = "survey"
    page_size = 30
    facets = [
        seeker.TermsFacet("survey.keyword", label = "Survey"),
        seeker.YearHistogram("published_date", label = "Published"),
        seeker.TermsFacet("group_id.keyword", label = "Group"),
        seeker.TermsFacet("category.cat.keyword", label = "Category"),
        seeker.TermsFacet("category.subcat.keyword", label = "Sub-Category"),
        seeker.TermsFacet("stage.keyword", label = "Stage"),
        seeker.TermsFacet("country.keyword", label = "Country"),
        seeker.TermsFacet("regions.keyword", label = "Region", visible_pos=0),
        seeker.TermsFacet("city.keyword", label = "City", visible_pos=0),
        seeker.TermsFacet("gender.keyword", label = "Gender"),
        seeker.TermsFacet("ethnics.keyword", label = "Ethnics", visible_pos=0),
        seeker.TermsFacet("income.keyword", label = "Income", visible_pos=0),
        seeker.TermsFacet("age.keyword", label = "Age"),
        #seeker.RangeFilter("age", label = "Age"),
        seeker.TermsFacet("cluster.keyword", label = "Cluster"),
        seeker.TermsFacet("brand.keyword", label = "Brand"),
        seeker.TermsFacet("product_form.keyword", label = "Product Form"),
        seeker.TermsFacet("method.keyword", label = "Method"),
        seeker.TermsFacet("blindcode.keyword", label = "Blind Code"),
        seeker.TermsFacet("olfactive.keyword", label = "Olfactive"),
        seeker.TermsFacet("perception.keyword", label = "Perception"),
        seeker.TermsFacet("liking.keyword", label = "Liking/Hedonics", order={"_key":"desc"}),
        seeker.TermsFacet("freshness", label = "Freshness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("cleanliness", label = "Cleanliness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("lastingness", label = "Lastingness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("intensity", label = "Intensity", visible_pos=0, order={"_key":"desc"}),
        seeker.OptionFacet("affective", label = "Affective", nestedfield="affective", visible_pos=0),
        seeker.OptionFacet("ballot", label = "Ballot", nestedfield="ballot", visible_pos=0),
        seeker.OptionFacet("behavioral", label = "Behavioral", nestedfield="behavioral", visible_pos=0),
        seeker.OptionFacet("children", label = "Children", nestedfield="children", visible_pos=0),
        seeker.OptionFacet("concept", label = "Concept", nestedfield="concept", visible_pos=0),
        seeker.OptionFacet("descriptors", label = "Descriptors", nestedfield="descriptors", visible_pos=0),
        seeker.OptionFacet("descriptors1", label = "Descriptors1", nestedfield="descriptors1", visible_pos=0),
        seeker.OptionFacet("descriptors2", label = "Descriptors2", nestedfield="descriptors2", visible_pos=0),
        seeker.OptionFacet("descriptors3", label = "Descriptors3", nestedfield="descriptors3", visible_pos=0),
        seeker.OptionFacet("descriptors4", label = "Descriptors4", nestedfield="descriptors4", visible_pos=0),
        seeker.OptionFacet("emotion", label = "Emotion", nestedfield="emotion", visible_pos=0),
        seeker.OptionFacet("fragrattr", label = "Fragr Attr", nestedfield="fragrattr", visible_pos=0),
        seeker.OptionFacet("hedonics", label = "Hedonics", nestedfield="hedonics", visible_pos=0),
        seeker.OptionFacet("imagine", label = "imagine", nestedfield="imagine", visible_pos=0),
        seeker.OptionFacet("mood", label = "Mood", nestedfield="mood", visible_pos=0),
        seeker.OptionFacet("physical", label = "Physical", nestedfield="physical", visible_pos=0),
        seeker.OptionFacet("smell", label = "Smell", nestedfield="smell", visible_pos=0),
        seeker.OptionFacet("suitable_product", label = "Suitability Product", nestedfield="suitable_product", visible_pos=0),
        seeker.OptionFacet("suitable_stage", label = "Suitability Stage", nestedfield="suitable_stage", visible_pos=2),
        seeker.OptionFacet("fit_descriptors1", label = "Fit Descriptors1", nestedfield="fit_descriptors1", visible_pos=0),
        seeker.OptionFacet("fit_descriptors2", label = "Fit Descriptors2", nestedfield="fit_descriptors2", visible_pos=0),
        seeker.OptionFacet("fit_descriptors3", label = "Fit Descriptors3", nestedfield="fit_descriptors3", visible_pos=0),
        seeker.OptionFacet("fit_descriptors4", label = "Fit Descriptors4", nestedfield="fit_descriptors4", visible_pos=0),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Benchmark", input="keywords_k"),
        ];
    #display = [
    #    "gender",
    #    "age",
    #    'brand',
    #    "blindcode",
    #    "freshness",
    #    ]
    exclude = [
        "resp_id",
        ]
    field_labels = {
        "question_p"    : "Question",
        }
    summary = [
        ]
    sumheader = ['brand']
    SUMMARY_URL="https://iffconnect.iff.com?id={0}"
    
    tabs = {'results_tab': '', 'summary_tab': 'hide', 'storyboard_tab': 'active', 'insights_tab': '' }
    decoder = None

    ### GLOBAL VARIABLES
             
scrape_li = []
posts_df = DataFrame()
search_keywords = {}

scrape_q = queue.Queue()



