"""
Definition of models.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.utils.encoding import python_2_unicode_compatible

# Create your models here.
import queue
import datetime
from collections import OrderedDict
from pandas import DataFrame

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl import DocType, Date, Double, Long, Integer, Boolean
from elasticsearch_dsl.connections import connections

import seeker
import FMI.settings

###
### EcoSystem
###

ecosystem_dashboard = {
    'company_keyword_table' : {
        'chart_type'  : "Table",
        'chart_title' : "Company / Keyword Doc Count",
        'data_type'  : "aggr",
        'listener'    : {'select' : {'rowsort': None}},
        'X_facet'     : {
            'field'   : "company.keyword",
            'label'   : "Company" },
        'Y_facet'     : {
            'field'   : "facet_keyword",
            'label'   : "Keywords" },
        },
    "aop_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Area of Potential",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "aop.keyword",
            'label'   : "Area of Potential" },
        },
    "role_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Role",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "role.keyword",
            'label'   : "Role" },
        },
    "keyword_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Keyword Doc Count",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "facet_keyword",
            'label'   : "Keywords" },
        },
    }

###
### IngrMolecules
###

ingr_molecules_dashboard = {
    'bucket_col' : {
        'chart_type'  : "ColumnChart",
        'chart_title' : "Flavor Class",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'X_facet'     : {
            'field'   : "bucket.keyword",
            'label'   : "Flavor Class",
            },
        'options'   : {
            #'hAxis'     : {'title': 'Flavor Class',  'textStyle' : { 'fontSize': 7}},
            'vAxis'     : {'title': 'Molecules #'}
            }
        },
    "regulator_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Regulator",
        'data_type'  : "facet",
        'controls'    : ['CategoryFilter'],
        'X_facet'     : {
            'field'   : "regulator.keyword",
            'label'   : "Regulator" },
        },
    "year_line" : {
        'chart_type'  : "ColumnChart",
        'chart_title' : "Year Ingr Created",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'X_facet'     : {
            'field'   : "year",
            'label'   : "Year",
            'total'   : False,
            },
        'options'   : {
            #'hAxis'     : {'title': 'Year'},
            'vAxis'     : {'title': 'Molecules #'}
            },

        },
    "keyword_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Keyword Doc Count",
        'data_type'  : "facet",
        'controls'    : ['CategoryFilter'],
        'X_facet'     : {
            'field'   : "facet_keyword",
            'label'   : "Keywords" },
        },
    "uptake_line" : {
        'chart_type': "ComboChart",
        'chart_title' : "Excito-Meter",
        'data_type'  : "card_uptake",
        #'controls'    : ['CategoryFilter'],
        'controls'    : ['NumberRangeFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "periods",
            'label'   : "Years since inception",
            'total'   : False,
            },
        'Y_facet'     : {
            'field'   : "uptake",
            'label'   : "Uptake",
            },
        'options'   : {
            "seriesType" : 'line',
            #"series"  : {0: {"type": 'bars'},},
            "series"  : {0: {"type": 'line', 'lineWidth': 6 },},
            'curveType' : 'function',
            'legend'    : { 'position': 'right' },
            'height'    : 600,
            'hAxis'     : {'title': 'Years since inception'},
            #'vAxis'    : {'viewWindow' : {'min': 0.0, 'max': 1.0}}
            'vAxis'     : {'viewWindow' : {'min': 0.0}, 'title': 'Percent Uptake'}
            },
        }
    }

###
### Patents
###

patents_dashboard = {
    'assignee_keyword_table' : {
        'chart_type'  : "Table",
        'chart_title' : "Assignee / Keyword Hits",
        'data_type'  : "aggr",
        'listener'    : {'select' : {'rowsort': None}},
        'X_facet'     : {
            'field'   : "assignee.keyword",
            'label'   : "Assignee" },
        'Y_facet'     : {
            'field'   : "facet_keyword",
            'label'   : "Keywords" },
        },
    "facet_comp_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Competitors Hits",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "facet_comp",
            'label'   : "Competitors" },
        },
    "published_keyword_line" : {
        'chart_type'  : "LineChart",
        'chart_title' : "Published Month Hits",
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
    "keyword_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Keyword Doc Count",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "facet_keyword",
            'label'   : "Keywords" },
        },
    }

###
### Sensory
###

sensory_dashboard = {
    "age_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Age",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "age.keyword",
            'label'   : "Age" },
        },
    "cand_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Candidate",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate" },
        },
    "cand_hedonics_col" : {
        'chart_type': "ComboChart",
        'chart_title' : "Consumer Hedonics Candidates",
        'data_type'   : "aggr",
        'controls'    : ['CategoryFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "hedonics.val.keyword",
            'question': "hedonics",
            "answers" : ["Liking Smell","Liking Taste", "Smell Intensity", "Taste Intensity"],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            "a-mean"  : True,
            'label'   : "Sensory Hedonics"
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {4: {"type": 'line'}}
            },
        },
    "cand_hedonics_table" : {
        'chart_type': "Table",
        'chart_title' : "Hedonics",
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
            'field'   : "hedonics.val.keyword",
            'question': "hedonics",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            'label'   : "Hedonics"
            },
        'options'     : {
            #'sort'    : 'event',
            'frozenColumns' : 2, # will be adjusted by bind_aggr
            },
        },
    "cand_perception_col" : {
        'chart_type': "ComboChart",
        'chart_title' : "Perception Candidates",
        'data_type'   : "aggr",
        'controls'    : ['CategoryFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "perception.val.keyword",
            'question': "sensory",
            "answers" : ["Elaborated","Richness","Balanced","Appetizing", "Recognizable"],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            "a-mean"  : True,
            'label'   : "Perception"
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {3: {"type": 'line'}}
            },
        },
    "cand_perception_table" : {
        'chart_type': "Table",
        'chart_title' : "Perception",
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
            'field'   : "perception.val.keyword",
            'question': "perception",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            'label'   : "Perception"
            },
        'options'     : {
            #'sort'    : 'event',
            'frozenColumns' : 2, # will be adjusted by bind_aggr
            },
        },
    "cand_sensory_attr_col" : {
        'chart_type': "ComboChart",
        'chart_title' : "Sensory Attr Candidates",
        'data_type'   : "aggr",
        'controls'    : ['CategoryFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "sensory_attr.val.keyword",
            'question': "sensory",
            "answers" : ["Meaty  HVP","Meaty Sulfury","Meaty Meaty"],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            "a-mean"  : True,
            'label'   : "Sensory Attr"
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {3: {"type": 'line'}}
            },
        },
    "cand_sensory_hedonics_col" : {
        'template'    : "cand_sensory_attr_col",
        'chart_type': "ComboChart",
        'chart_title' : "Sensory Hedonics Candidates",
        'data_type'   : "aggr",
        'controls'    : ['CategoryFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "sensory_hedonics.val.keyword",
            'question': "sensory_hedonics",
            "answers" : ["Saltiness","Sweetness", "Umami"],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            "a-mean"  : True,
            'label'   : "Sensory Hedonics"
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {3: {"type": 'line'}}
            },
        },
    "cand_taste_col" : {
        'chart_type': "ComboChart",
        'chart_title' : "Taste Candidates",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'help'        : "Select Row for sorting, Select Column Header for filter",
        'listener'    : {'select' : {'colsort': None, 'rowcolfilter': ["sensory_attr_cand_radar", "sensory_hedonics_cand_radar", "perception_cand_radar", "hedonics_cand_radar"]}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "taste",
            'label'   : "Taste" },
        'result'      : {
            "q-mean"  : "taste", # series name
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
            },
        },
    "cand_smell_col" : {
        'chart_type': "ComboChart",
        'chart_title' : "Smell Candidates",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'help'        : "Select Row for sorting, Select Column Header for filter",
        'listener'    : {'select' : {'colsort': None, 'rowcolfilter': ["sensory_attr_cand_radar", "sensory_hedonics_cand_radar", "perception_cand_radar", "hedonics_cand_radar"]}},
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "smell",
            'label'   : "Smell" },
        'result'      : {
            "q-mean"  : "smell", # series name
            },
        'options'     : {
            "seriesType" : 'bars',
            "series"  : {1: {"type": 'line'}, 2: {"type": 'line'}}
            },
        },
    "consumption_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Consumption",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "consumption.keyword",
            'label'   : "Consumption" },
        },
    "country_map" : {
        'chart_type'  : "GeoChart",
        #'data_type'  : 'aggr',
        'data_type'   : 'facet',
        'chart_title' : "Country Resp Count",
        'listener'    : {'select' : {'select_event': 'mdt_country_sel'}},
        'X_facet'     : {
            'field'   : "country.keyword",
            'total'   : True,
            'label'   : "Country" },
        },
    "hedonics_cand_radar" : {
        'chart_type'  : "RadarChart",
        'chart_title' : "Hedonics",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "hedonics.val.keyword",
            'question': "hedonics",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            'label'   : "Hedonics"
            },
        'options'     : {
            'width'   : 300,
            'height'  : 300
            },
        },
    "sensory_attr_cand_radar" : {
        'chart_type'  : "RadarChart",
        'chart_title' : "Sensory Attributes",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "sensory_attr.val.keyword",
            'question': "sensory_attr",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            'label'   : "Sensory Attributes"
            },
        'options'     : {
            'width'   : 300,
            'height'  : 300
            },
        },
    "sensory_hedonics_cand_radar" : {
        'chart_type'  : "RadarChart",
        'chart_title' : "Sensory Hedonics",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "sensory_hedonics.val.keyword",
            'question': "sensory_hedonics",
            "answers" : [], # All
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            'label'   : "BT"
            },
        'options'     : {
            'width'   : 300,
            'height'  : 300
            },
        },
    "perception_cand_radar" : {
        'chart_type'  : "RadarChart",
        'chart_title' : "Perception",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'X_facet'     : {
            'field'   : "blindcode.keyword",
            'label'   : "Candidate",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "perception.val.keyword",
            'question': "perception",
            "answers" : [], # All
            "values"  : [{'v-sum':'*'}],
            "metric"  : "prc",
            'label'   : "Perception"
            },
        'options'     : {
            'width'   : 300,
            'height'  : 300
            },
        },
    "country_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Country",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "country.keyword",
            'label'   : "Respondent" },
        },
    "ttest_table" : {
        'chart_type'  : "Table",
        'chart_title' : "t-test Spices - Candidate",
        'data_type'   : "card_ttest",
        'controls'    : ['CategoryFilter'],
        "significance": 0.2, # 0.2 = 80%
        "test_type"   : "two-tailed",
        'X_facet'     : {
            'field'   : "blindcode", # no keyword, based on hits
            'label'   : "Candidate"
            },
        'Y_facet'     : {
            'field'   : "hedonics", # no keyword, based on hits
            'question': "hedonics",
            "answers" : ["Spices"],
            "values"  : [{'v-sum':'*'}],
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


###
### Workbooks and ES Index
###

es_indicis = {
    'ecosystem' : {
        'document'      : "ecosystem",
        'index'         : "excel_ecosystem",
        'doc_type'      : "ecosystem",
        'properties' : {
            'subset'        : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'aop'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'role'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'name'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'url'           : {'type' : 'text'},
            'why'           : {'type' : 'text'},
            'how'           : {'type' : 'text'},
            'what'          : {'type' : 'text'},
            'where'         : {'type' : 'text'},
            'country'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'contacts'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'company'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            },
        # SEEKER
        'page_size'     :30,
        'facets' : [
            seeker.TermsFacet("aop.keyword", label = "Area of Potential"),
            seeker.TermsFacet("role.keyword", label = "Role"),
            seeker.TermsFacet("country.keyword", label = "Country"),
            seeker.TermsFacet("company.keyword", label = "company"),
            ],
        'facets_keyword' : [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")],
        'display'       : ["company","aop", "role", "why", "how", "what"],
        'sort'          : [],
        'summary'       : ['why', 'how', 'what'],
        'sumheader'     : ['company'],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {"company" : ""},
        'tabs'          : {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'},
        },
    'ingr_molecules' : {
        'document'      : "ingr_molecules",
        #'using'        : client,
        'index'         : "excel_ingr_molecules",
        'doc_type'      : "ingr_molecules",
        'properties' : {
            'IPC'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'name'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'uptake'        : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'year'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'nr_of_IPCs'    : {'type' : 'integer'},
            'nr_of_IPCs_SC' : {'type' : 'integer'},
            'selling_IPCs'  : {'type' : 'integer'},
            'FITTE_score'   : {'type' : 'float'},
            'FITTE_norm'    : {'type' : 'float'},
            'regions'       : {'type' : 'integer'},
            'flavor_classes' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'sales_val'     : {'type' : 'float'},
            'sales_vol'     : {'type' : 'float'},
            'tech_vol'      : {'type' : 'float'},
            'bucket'        : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'cost'          : {'type' : 'float'},
            'use_level'     : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'low_medium_high' : {'type' : 'float'},
            'CIU'           : {'type' : 'float'},
            'regulator'     : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            },
        # SEEKER
        'page_size'     :30,
        'facets'        : [
            seeker.TermsFacet("IPC.keyword", label = "IPC", visible_pos=0),
            seeker.TermsFacet("name.keyword", label = "Name", visible_pos=0),
            seeker.TermsFacet("uptake.keyword", label = "Uptake", visible_pos=0),
            seeker.TermsFacet("year.keyword", label = "Year", visible_pos=0, order={"_key":"asc"}),
            seeker.TermsFacet("bucket.keyword", label = "Bucket", visible_pos=0),
            seeker.TermsFacet("flavor_classes.keyword", label = "Flavor Classes", visible_pos=0),
            seeker.TermsFacet("regulator.keyword", label = "Regulator", visible_pos=0),
            ],
        'facets_keyword' : [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")],
        'display'       : ["IPC", "name", "year", "bucket", "FITTE_norm", "CIU", "regulator"],
        'sort'          : [],
        'summary'       : [],
        'sumheader'     : [],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {},
        'tabs'          : {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'},
        },
    'patents' : {
        'document'      : "patents",
        'index'         : "excel_patents",
        'doc_type'      : "patents",
        'properties' : {
            'category'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'publication'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'assignee'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'assignee_DWPI' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'title'         : {'type' : 'text'},
            'title_DWPI'    : {'type' : 'text'},
            'url'           : {'type' : 'text'},
            'published_date': {'type' : 'date'},
            'abstract'      : {'type' : 'text'}
            },
        # SEEKER
        'page_size'     :30,
        'facets' : [
            seeker.TermsFacet("category.keyword", label = "Category"),
            seeker.DayHistogram("published_date", label = "Published"),
            seeker.TermsFacet("assignee.keyword", label = "Assignee"),
            ],
        'facets_keyword' : [
            seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
            seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                                initial="International Flavors & Fragrances, Symrise, Givaudan, Firmenich, Frutarom")],
        'display'       : ["title","category", "assignee", "publication", "published_date"],
        'sort'          : [],
        'summary'       : ['title', 'abstract'],
        'sumheader'     : ['title'],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {"title" : "", "publication" : ""},
        'tabs'          : {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'},
        },
    'sensory' : {
        'document'      : "sensory",
        'index'         : "sensory",
        'doc_type'      : "sensory",
        'properties' : {
            'subset'        : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'country'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'category'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'base'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'flavor_name'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'published_date': {'type' : 'date'},
            'creative_center' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'stage'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'resp_id'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'blindcode'    : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'sensory_attr' : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    }
                                },
            'sensory_hedonics' : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    }
                                },
            'perception'   : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    }
                                },
            'smell'        : {'type' : 'float'},
            'taste'        : {'type' : 'float'},
            'gender'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'age'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'consumption'  : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'brand'        : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
            'choice'       : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    }
                                },
            'describe'     : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    }
                                },
            'hedonics'     : {'type'       : 'nested',
                                'properties' : {
                                    'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                    'prc' : {'type' : 'float'},
                                    },
                                },
            },
        # SEEKER
        'page_size'     :30,
        'facets' : [
            seeker.TermsFacet("subset.keyword", label = "Subset"),
            seeker.TermsFacet("country.keyword", label = "Country"),
            seeker.TermsFacet("blindcode.keyword", label = "Product"),
            seeker.TermsFacet("category.keyword", label = "Category"),
            seeker.TermsFacet("flavor_name.keyword", label = "Flavor Name"),
            seeker.TermsFacet("creative_center.keyword", label = "Creative Center"),
            seeker.TermsFacet("stage.keyword", label = "Stage"),
            seeker.YearHistogram("published_date", label = "Published"),
            seeker.TermsFacet("resp_id.keyword", label = "Respondent"),
            seeker.RangeFilter("smell", label = "Smell"),
            seeker.RangeFilter("taste", label = "Taste"),
            seeker.NestedFacet("sensory_attr.val.keyword", label = "Sensory Attr", nestedfield="sensory_attr"),
            seeker.NestedFacet("sensory_hedonics.val.keyword", label = "Sensory Hedonics", nestedfield="sensory_hedonics"),
            seeker.NestedFacet("perception.val.keyword", label = "Perception", nestedfield="perception"),
            seeker.TermsFacet("age.keyword", label = "Age"),
            seeker.TermsFacet("gender.keyword", label = "Gender"),
            seeker.TermsFacet("consumption.keyword", label = "Consumption"),
            seeker.TermsFacet("brand.keyword", label = "Brand"),
            seeker.NestedFacet("choice.val.keyword", label = "Choice", nestedfield="choice"),
            seeker.NestedFacet("describe.val.keyword", label = "Describe", nestedfield="describe"),
            seeker.NestedFacet("hedonics.val.keyword", label = "Hedonics", nestedfield="hedonics"),
            ],
        'facets_keyword' : [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")],
        'display'       : ["subset", "blindcode", "stage", "resp_id", "smell", "taste"],
        'sort'          : [],
        'summary'       : [],
        'sumheader'     : [],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {},
        'tabs'          : {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'},
        },
    'brugger_xinumber' : {
        'document'      : "ssyvret_xinumber",
        #'using'        : client,
        'index'         : "excel_ssyvret_xinumber",
        'doc_type'      : "ssyvret_xinumber",
        'properties' : 
         {"ACCESSKEY":{"type":"float"},
		"ACCESS_TYPE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"ACTIVEITEMS":{"type":"float"},
		"ADDEDBY":{"type":"text", "fields":{"keyword":{"type":"keyword","ignore_above":256}}},
		"ADMIN_MODE":{"type":"text","fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"APPLICATION":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"BASENUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"BASE_TYPE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"BOOKNUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CANROLLUP_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CAN_FORWARD":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CBALIASCODE":{"type":"float"}, 
		"CBOOKID":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CHANGEDBY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CHKRESID":{"type":"float"}, 
		"CMPD_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"COLOR":{"type":"float"}, 
		"COMMENTS":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}}, 
		"COMPANYID":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"COMPLEXITY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"COST_CURRENCY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"COST_WTUOM":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"COUNTRY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CREATEDBY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CREATORID":{"type":"float"}, 
		"CREDIT_LIST":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CUSTNAME":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"CUSTOMER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATEADDED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATECHANGED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATELASTCOSTED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATE_CREATED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATE_MODIFIED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATE_REFERENCED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATE_REG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DATE_SAMPLE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DEFSOLVNUM":{"type":"float"}, "DENSITY":{"type":"float"},
		"DENSITY_VOLUOM":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}}, 
		"DENSITY_WTUOM":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DERIVED_FROM":{"type":"text",  "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DESCRIPTION":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DNU_FLAG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DUPLICATIONOF":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"DUPLICATION_OF":{"type":"float"}, 
		"DUPSMPL_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"EXPORTED_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"FF_FAMILY":{"type":"float"},
		"FF_SUBFAMILY":{"type":"float"},
		"FLASHPOINT":{"type":"float"},
		"FRMLID":{"type":"long"},
		"FRMLNAME":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"FRML_FORM":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"FRML_TYPE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"FROM_MFG_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"GRAS_FLAG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"HASBYPRODS_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"HASCOMMENTS_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"HASSUBF_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"ICHECK_STATUS":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"IMPORTED_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"INOTHERS_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"IS_TEMPCOPY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"KOSHER_TYPE":{"type":"float"},
		"LINEITEMS":{"type":"float"},
		"MAX_USAGE":{"type":"float"},
		"MFGLOCATION":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"MFGNUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"MIN_USAGE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"MOD_REASON":{"type":"float"},
		"NATIDENT_FLAG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"NATURAL_FLAG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"ONSERVER_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"ORGANIC_TYPE":{"type":"float"},
		"OWNEDBY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"PARTS":{"type":"float"},
		"PRIVATE_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"PRI_COST":{"type":"float"},
		"PROFID":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"PROFILENUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"PROFILETITLE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"PROJNUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"REPLACED_WITH":{"type":"float"},
		"RESTRICTED":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SEC_COST":{"type":"float"},
		"SENSKIN_FLAG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SENTTO_MFG_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SIMILARTO":{"type":"float"},
		"SMPLCHG_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SOLUBILITY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SOLVENTS":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SSUBS_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"STAGE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"SUBFRML_CNT":{"type":"long"},
		"SUBFRML_ITEMS":{"type":"long"},
		"SUBFRML_MAXLEVEL":{"type":"long"},
		"SUBMIT_DATE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"TOBE_FIXED_BY":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"TSUBS_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"USAGE":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"USERNUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"VALIDPCOST_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"VALIDSCOST_FLG":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"VERSION_NUM":{"type":"long"},
		"VERSION_OF":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"XINUMBER":{"type":"text", "fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
		"subset":{"type":"text","fields":{"keyword":{"type":"keyword", "ignore_above":256}}},
            },
        # SEEKER
        'page_size'     :30,
        'facets'        : [
            seeker.TermsFacet("XINUMBER.keyword", label = "XINUMBER", visible_pos=0),
            seeker.TermsFacet("BOOKNUMBER.keyword", label = "BOOKNUMBER", visible_pos=0),
            seeker.TermsFacet("FRMLNAME.keyword", label = "FRMLNAME", visible_pos=0, order={"_key":"asc"}),
            seeker.TermsFacet("FRML_TYPE.keyword", label = "FRML_TYPE", visible_pos=0),
            seeker.TermsFacet("OWNEDBY.keyword", label = "OWNEDBY ", visible_pos=0),
            seeker.TermsFacet("SEC_COST.keyword", label = "SEC_COST", visible_pos=0),
            ],
        'facets_keyword' : [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")],
        'display'       : ["XINUMBER", "BOOKNUMBER", "FRMLNAME", "FRML_TYPE", "OWNEDBY", "SEC_COST", "APPLICATION"],
        'sort'          : [],
        'summary'       : [],
        'sumheader'     : [],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {},
        'tabs'          : {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'},
        }
    }

workbooks = {
    'ecosystem' : {
        'es_index'      : es_indicis['ecosystem'],
        'url'           : '/search_workbook?',
        'display'       : [],
        'facets'        : ["aop.keyword", "role.keyword", "country.keyword", "company.keyword"],
        'tiles'         : [],
        'charts'        : ecosystem_dashboard,
        'storyboards'   : {
            'initial' : [
                    {'name'     : 'initial',
                     'layout'   : OrderedDict([
                        ('table1', [["aop_pie", "keyword_pie"], ["role_col"]]),
                        ('table2', [["company_keyword_table"]])])}
                ]
            },
        'filters'       : {}
        },
    'ingr_molecules' : {
        'es_index'      : es_indicis['ingr_molecules'],
        'url'           : '/search_workbook?',
        'display'       : ["IPC", "name", "uptake", "year", "bucket", "FITTE_norm", "CIU", "regulator"],
        'facets'        : ["IPC.keyword", "name.keyword", "uptake.keyword", "year.keyword", "bucket.keyword", "flavor_classes.keyword", "regulator.keyword"],
        'tiles'         : ["year.keyword", "regulator.keyword", "bucket.keyword", "flavor_classes.keyword"],
        'charts'        : ingr_molecules_dashboard,
        'dashboard_data': 'pull',
        'storyboards'   : {
            'initial' : [
                    {'name'     : 'molecules',
                     'layout'   : OrderedDict([
                         ('table1', [["year_line", "bucket_col"]]),
                         ('table2', [["regulator_pie", "keyword_pie"]])])},
                    {'name'     : 'excito-meter',
                    'layout'    : OrderedDict([
                        ('table', [['uptake_line']])])}
                ]
            },
        'filters'       : {}
        },
    'patents' : {
        'es_index'      : es_indicis['patents'],
        'url'           : '/search_workbook?',
        'display'       : ["title","category", "assignee", "publication", "published_date"],
        'facets'        : ["category.keyword", "published_date", "assignee.keyword"],
        'tiles'         : ["category"],
        'charts'        : patents_dashboard,
        'storyboards'   : {
            'initial' : [
                    {'name'     : 'initial',
                     'layout'   : OrderedDict([
                        ('table1', [["published_keyword_line"]]),
                        ('table2', [["facet_comp_pie", "keyword_pie"], ["assignee_keyword_table"]])])}
                ]
            },
        'filters'       : {}
        },
    'sensory' : {
        'es_index'      : es_indicis['sensory'],
        'url'           : '/search_workbook?',
        'display'       : ["blindcode", "stage", "resp_id", "smell", "taste", "sensory_attr", "sensory_hedonics"],
        'facets'        : ["subset.keyword", "country.keyword", "blindcode.keyword", "category.keyword", "category.keyword", "flavor_name.keyword",
                           "sensory_attr.val.keyword", "sensory_hedonics.val.keyword", "perception.val.keyword",
                           "age.keyword", "gender.keyword", "consumption.keyword", "brand.keyword", "hedonics.val.keyword"],
        'tiles'         : ["country.keyword", "category.keyword", "age.keyword", "gender.keyword", "blindcode.keyword"],
        'charts'        : sensory_dashboard,
        'dashboard_data': 'pull',
        'storyboards'   : {
            'initial' : [
                    {'name'     : 'Candidates',
                     'layout'   : OrderedDict([
                         ('table1', [["country_pie", "cand_col"]]),
                         ('table2', [["cand_hedonics_col"], ["cand_sensory_hedonics_col"]])])},
                    {'name'     : 'Consumer',
                     'layout'   : OrderedDict([
                         ('table1', [["age_pie", "consumption_col"]]),
                         ('table2', [["cand_hedonics_table"], ["cand_perception_table"]])])},
                    {'name'     : 'Sensory',
                    'layout'    : OrderedDict([
                        ('table', [["cand_sensory_attr_col"],["cand_sensory_hedonics_col"]])])},
                    {'name'     : 'Profile Taste',
                    'layout'    : OrderedDict([
                        ('table', [['cand_taste_col'],['sensory_attr_cand_radar', 'sensory_hedonics_cand_radar'], ['perception_cand_radar', 'hedonics_cand_radar']])])},
                    {'name'     : 'Profile Smell',
                    'layout'    : OrderedDict([
                        ('table', [['cand_smell_col'],['sensory_attr_cand_radar', 'sensory_hedonics_cand_radar'], ['perception_cand_radar', 'hedonics_cand_radar']])])},
                    {'name'     : 'Insights',
                    'layout'    : OrderedDict([
                        ('table', [['ttest_table']])])}],
            'mdt_filters' : [
                    {'name'     : "mdt_filters_globe",
                     'layout'   : OrderedDict({'rows': [['country_map']]})}],
            'mdt_consumer' : [
                    {'name'     : 'mdt_consumer',
                     'layout'   : OrderedDict([
                         ('table1', [["age_pie", "consumption_col"]]),
                         ('table2', [["cand_perception_col"], ["cand_hedonics_table"], ["cand_perception_table"]])])}],
            'mdt_sensory' : [
                    {'name'     : 'mdt_sensory',
                    'layout'    : OrderedDict([
                        ('table', [["cand_sensory_attr_col"],["cand_sensory_hedonics_col"]])])}],
            'mdt_profile' : [
                    {'name'     : 'mdt_profile_taste',
                    'layout'    : OrderedDict([
                        ('table', [['cand_taste_col'],['sensory_attr_cand_radar', 'sensory_hedonics_cand_radar'], ['perception_cand_radar', 'hedonics_cand_radar']])])},
                    {'name'     : 'mdt_profile_smell',
                    'layout'    : OrderedDict([
                        ('table', [['cand_smell_col'],['sensory_attr_cand_radar', 'sensory_hedonics_cand_radar'], ['perception_cand_radar', 'hedonics_cand_radar']])])}],
            'mdt_insights' : [
                    {'name'     : 'mdt_insights',
                    'layout'    : OrderedDict([
                        ('table', [['ttest_table']])])},
                ]
            },
        'filters'       : {}
        },
    'brugger_xinumber' : {
        'es_index'      : es_indicis['brugger_xinumber'],
        'url'           : '/search_workbook?',
        'display'       : ["XINUMBER", "BOOKNUMBER", "FRMLNAME", "FRML_TYPE", "OWNEDBY", "SEC_COST"],
        'facets'        : ["XINUMBER.keyword", "BOOKNUMBER.keyword", "FRMLNAME.keyword", "FRML_TYPE.keyword", "OWNEDBY.keyword", "SEC_COST.keyword"],
        'tiles'         : ["XINUMBER.keyword", "BOOKNUMBER.keyword", "FRMLNAME.keyword", "FRML_TYPE.keyword"],
        'charts'        : {},
        'filters'       : {}
        }
    }

