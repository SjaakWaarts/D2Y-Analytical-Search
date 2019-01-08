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
### EcoSystem Dashboard
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
### Patents Dashboard
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
### Sensory Dashboard
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
### TMLO Dashboard
###

tmlo_dashboard = {
    "aggregatieniveau_pie" : {
        'chart_type': "PieChart",
        'chart_title' : "Aggregatieniveau",
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "Aggregatieniveau",
            'label'   : "Aggregatieniveau" },
        },
    "vorm_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Vorm",
        'controls'    : ['CategoryFilter'],
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "Vorm.GenreOfRedactie.keyword",
            'label'   : "Genre of Redactie" },
        },
    "vorm_omvang_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Omvang / Vorm",
        'controls'    : ['CategoryFilter'],
        'data_type'  : "aggr",
        'X_facet'     : {
            'field'   : "Vorm.GenreOfRedactie.keyword",
            'label'   : "Genre of Redactie",
            'total'   : False},
        'Y_facet'     : {
            'field'   : "Bestanden.Formaten.Omvang",
            'label'   : "Omvang"} # will be overwritten by the metric facet label,
        },
    "formaat_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Formaat",
        'controls'    : ['CategoryFilter'],
        'data_type'  : "facet",
        'X_facet'     : {
            'field'   : "Bestanden.Formaten.Bestandsformaat",
            'label'   : "Bestand Formaat" },
        },
    "aggr_openbaarheid_table" : {
        'chart_type': "Table",
        'chart_title' : "Openbaarheid",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'listener'    : {'select' : {'rowsort': None}},
        'X_facet'     : {
            'field'   : "Aggregatieniveau",
            'label'   : "Aggregatieniveau",
            'total'   : True
            },
        'Y_facet'     : {
            'field'   : "Openbaarheid.Indicatie",
            'question': "Openbaarheid",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            'label'   : "Openbaarheid"
            },
        'options'     : {
            #'sort'    : 'event',
            'frozenColumns' : 2, # will be adjusted by bind_aggr
            },
        },
    "aggr_vertrouwelijkheid_table" : {
        'chart_type': "Table",
        'chart_title' : "Vertrouwelijkheid",
        'data_type'  : "aggr",
        'controls'    : ['CategoryFilter'],
        'transpose'   : True,
        'listener'    : {'select' : {'rowsort': None}},
        'X_facet'     : {
            'field'   : "Aggregatieniveau",
            'label'   : "Aggregatieniveau",
            'total'   : True
            },
        'Y_facet'     : {
            'field'   : "Vertrouwelijkheid.Indicatie",
            'question': "Vertrouwelijkheid",
            "answers" : [],
            "values"  : [{'v-sum':'*'}],
            'label'   : "Vertrouwelijkheid"
            },
        'options'     : {
            #'sort'    : 'event',
            'frozenColumns' : 2, # will be adjusted by bind_aggr
            },
        },
        "aanmaak_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Aanmaak Year-Month",
            'data_type'  : "aggr",
            #'data_type'  : "facet",
            'controls'    : ['DateRangeFilter'],
            'X_facet'     : {
                'field'   : "Bestanden.Formaten.Datum-aanmaak",
                'label'   : "Aanmaak",
                'key'     : 'key_as_string',
                'total'   : True,
                'type'    : 'date'},
            #'Y_facet'     : {
            #    'field'   : "facet_keyword",
            #    'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM'},
                },
            },
    }

###
### TMLO Mapping
###

date_formatter = "year||year_month||year_month_day"

tmlo = {
        "Identificatiekenmerk": {
            'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}
        },
        "Aggregatieniveau": {
            "type": "keyword"
        },
        "Namen": {
            'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}
        },
        "Classificaties": {
            "type": "nested",
            "properties": {
                "Code": {
                    "type": "keyword"
                },
                "Omschrijving": {
                    "type": "text"
                },
                "Bron": {
                    "type": "text"
                },
                "Periode": {
                    "properties": {
                        "Begin": {
                            "type": "date",
                            "format": date_formatter
                        },
                        "Eind": {
                            "type": "date",
                            "format": date_formatter
                        }
                    }
                }
            }
        },
        "Omschrijvingen": {
            "type": "text"
        },
        "Locatie": {
            "properties": {
                "Fysiek": {
                    "type": "keyword",
                    "index": "false"
                },
                "Virtueel": {
                    "type": "keyword",
                    "index": "false"
                }
            }
        },
        "Dekkingen": {
            "type": "nested",
            "properties": {
                "Tijd": {
                    "properties": {
                        "Type": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Periode": {
                            "properties": {
                                "Begin": {
                                    "type": "date",
                                    "format": date_formatter
                                },
                                "Eind": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        }
                    }
                },
                "Geografisch": {
                    "properties": {
                        "Locatie_aanduiding": {
                            "type": "text"
                        },
                        "Adres": {
                            "properties": {
                                "Plaats": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Straat": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Huisnummer": {
                                    "type": "integer",
                                    "copy_to": "full_address"
                                },
                                "Letter": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Toevoeging": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Postcode": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Buurtkern": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Gemeente": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "Kadaster": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    },
                                    "copy_to": "full_address"
                                },
                                "full_address": {
                                    "type": "text"
                                }
                            }
                        },
                        "Geo-object": {
                            "properties": {
                                "Naam_object": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "ID_object": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Geometrie": {
                            "properties": {
                                "GML": {
                                    "properties": {}
                                },
                                "IGML": {
                                    "properties": {
                                        "RD_X_coordinaat": {
                                            "type": "float"
                                        },
                                        "RD_Y_coordinaat": {
                                            "type": "float"
                                        },
                                        "WSG_X_coordinaat": {
                                            "type": "float"
                                        },
                                        "WSG_Y_coordinaat": {
                                            "type": "float"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "ExterneIdentificatieKenmerken": {
            "type": "nested",
            "properties": {
                "Kenmerk": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "IdentificatieSysteem": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                }
            }
        },
        "Talen": {
            'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}
        },
        "EventGeschiedenis": {
            "type": "nested",
            "properties": {
                "Periode": {
                    "properties": {
                        "Begin": {
                            "type": "date",
                            "format": date_formatter,
                        },
                        "Eind": {
                            "type": "date",
                            "format": date_formatter,
                        }
                    }
                },
                "Type": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Beschrijving": {
                    "type": "text"
                },
                "Verantwoordelijke_functionaris": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Aanleiding": {
                    "type": "text"
                }
            }
        },
        "EventPlan": {
            "type": "nested",
            "properties": {
                "Periode": {
                    "properties": {
                        "Begin": {
                            "type": "date",
                            "format": date_formatter,
                        },
                        "Eind": {
                            "type": "date",
                            "format": date_formatter,
                        }
                    }
                },
                "Type": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Beschrijving": {
                    "type": "text"
                },
                "Verantwoordelijke_functionaris": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Aanleiding": {
                    "type": "text"
                }
            }
        },
        "Relaties": {
            "type": "nested",
            "properties": {
                "ID": {
                    "type": "keyword"
                },
                "Type": {
                    "type": "text"
                },
                "Periode": {
                    "properties": {
                        "Begin": {
                            "type": "date",
                            "format": date_formatter
                        },
                        "Eind": {
                            "type": "date",
                            "format": date_formatter
                        }
                    }
                }
            }
        },
        "Ontstaanscontexten": {
            "type": "nested",
            "properties": {
                "Actor": {
                    "properties": {
                        "Identificatiekenmerk": {
                            "type": "keyword"
                        },
                        "Aggregatieniveau": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Authorisatienaam": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Locatie": {
                            "type": "text"
                        },
                        "Jurisdictie": {
                            "type": "text"
                        }
                    }
                },
                "Activiteit": {
                    "properties": {
                        "Kenmerk": {
                            "type": "keyword"
                        },
                        "Aggregatieniveau": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Naam": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        }
                    }
                }
            }
        },
        "Gebruiksrecht": {
            "properties": {
                "Indicatie": {
                    "type": "boolean"
                },
                "Gebruiksrechtvoorwaarden": {
                    "type": "nested",
                    "properties": {
                        "Omschrijving": {
                            "type": "text"
                        },
                        "Periode": {
                            "properties": {
                                "Begin": {
                                    "type": "date",
                                    "format": date_formatter
                                },
                                "Eind": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        }
                    }
                }
            }
        },
        "Openbaarheid": {
            "properties": {
                "Indicatie": {
                    "type": "boolean"
                },
                "Openbaarheidsbeperkingen": {
                    "type": "nested",
                    "properties": {
                        "Omschrijving": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Periode": {
                            "properties": {
                                "Begin": {
                                    "type": "date",
                                    "format": date_formatter
                                },
                                "Eind": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        }
                    }

                }
            }
        },
        "Vorm": {
            "properties": {
                "GenreOfRedactie": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Structuur": {
                    "type": "text"
                },
                "Verschijningsvorm": {
                    "type": "text"
                }
            }
        },
        "Integriteit": {
            "properties": {
                "Kwaliteit": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Datum_vaststelling": {
                    "type": "date",
                    "format": date_formatter
                },
                "Toelichting": {
                    "type": "text"
                }
            }
        },
        "Bestanden": {
            "type": "nested",
            "properties": {
                "Formaten": {
                    "type": "nested",
                    "properties": {
                        "Identificatiekenmerk": {
                            "type": "keyword",
                        },
                        "Bestandsnaam": {
                            "properties": {
                                "Naam": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "Extensie": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                }
                            }
                        },
                        "Type": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Omvang": {
                            "type": "float"
                        },
                        "Bestandsformaat": {
                            "type": "keyword"
                        },
                        "Creatieapplicatie": {
                            "properties": {
                                "Naam": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "Versie": {
                                    "type": "keyword"
                                },
                                "Datum_aanmaak": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        },
                        "Fysieke-integriteit": {
                            "properties": {
                                "Algoritme": {
                                    "type": "text",
                                    "index": "false"
                                },
                                "Waarde": {
                                    "type": "text",
                                    "index": "false"
                                },
                                "Datum": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        },
                        "Datum-aanmaak": {
                            "type": "date",
                            "format": date_formatter
                        },
                        "EventPlan-formaat": {
                            "type": "nested",
                            "properties": {
                                "Periode": {
                                    "properties": {
                                        "Begin": {
                                            "type": "date",
                                            "format": date_formatter,
                                        },
                                        "Eind": {
                                            "type": "date",
                                            "format": date_formatter,
                                        }
                                    }
                                },
                                "Type": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "Beschrijving": {
                                    "type": "text"
                                },
                                "Verantwoordelijke_functionaris": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "Aanleiding": {
                                    "type": "text"
                                }
                            }
                        },
                        "Relaties": {
                            "type": "nested",
                            "properties": {
                                "ID": {
                                    "type": "keyword"
                                },
                                "Type": {
                                    "type": "text"
                                },
                                "Periode": {
                                    "properties": {
                                        "Begin": {
                                            "type": "date",
                                            "format": date_formatter
                                        },
                                        "Eind": {
                                            "type": "date",
                                            "format": date_formatter
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "Vertrouwelijkheid": {
            "properties": {
                "Indicatie": {
                    "type": "boolean"
                },
                "Vertrouwelijkheden": {
                    "type": "nested",
                    "properties": {
                        "Classificatieniveau": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "Periode": {
                            "properties": {
                                "Begin": {
                                    "type": "date",
                                    "format": date_formatter
                                },
                                "Eind": {
                                    "type": "date",
                                    "format": date_formatter
                                }
                            }
                        }
                    }
                }
            }

        },
        "x-customer-meta-profile": {
            "type": "keyword",
        },
        "x-customer-meta-domain": {
            "type": "keyword"
        },
        "x-customer-meta-target": {
            "type": "keyword"
        }
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
            seeker.PercFacet("sensory_attr.val.keyword", label = "Sensory Attr", nestedfield="sensory_attr"),
            seeker.PercFacet("sensory_hedonics.val.keyword", label = "Sensory Hedonics", nestedfield="sensory_hedonics"),
            seeker.PercFacet("perception.val.keyword", label = "Perception", nestedfield="perception"),
            seeker.TermsFacet("age.keyword", label = "Age"),
            seeker.TermsFacet("gender.keyword", label = "Gender"),
            seeker.TermsFacet("consumption.keyword", label = "Consumption"),
            seeker.TermsFacet("brand.keyword", label = "Brand"),
            seeker.PercFacet("choice.val.keyword", label = "Choice", nestedfield="choice"),
            seeker.PercFacet("describe.val.keyword", label = "Describe", nestedfield="describe"),
            seeker.PercFacet("hedonics.val.keyword", label = "Hedonics", nestedfield="hedonics"),
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
    'tmlo' : {
        'document'      : "tmlo",
        'index'         : "tmlo",
        'doc_type'      : "doc",
        'properties'    : tmlo,
        # SEEKER
        'page_size'     :30,
        'facets' : [
            seeker.TermsFacet("Aggregatieniveau", label="Aggregatieniveau"),
            seeker.TermsFacet("Openbaarheid.Indicatie", label="Openbaarheid"),
            seeker.TermsFacet("Vertrouwelijkheid.Indicatie", label="Vertrouwelijkheid"),
            seeker.TermsFacet("Vorm.GenreOfRedactie.keyword", label="Vorm"),
            seeker.NestedFacet("Classificaties.Code", label="Classificatie", nestedfield="Classificaties"),
            seeker.NestedFacet("Bestanden.Formaten.Bestandsformaat", label="Formaat", nestedfield="Bestanden.Formaten"),
            seeker.MetricFacet("Bestanden.Formaten.Omvang", label="Omvang", nestedfield="Bestanden.Formaten"),
            seeker.MonthHistogram("Bestanden.Formaten.Datum-aanmaak", label="Aanmaak", nestedfield="Bestanden.Formaten", date_formatter=date_formatter),
            ],
        'facets_keyword' : [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")],
        'display'       : ["Identificatiekenmerk", "Aggregatieniveau","Openbaarheid.Indicatie", "Namen"],
        'sort'          : [],
        'summary'       : [],
        'sumheader'     : [],
        'SUMMARY_URL'   : "{}",
        'urlfields'     : {"Identificatiekenmerk" : "http://www.divault.nl?{0}"},
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
    'tmlo' : {
        'es_index'      : es_indicis['tmlo'],
        'url'           : '/search_workbook?',
        'display'       : ["Identificatiekenmerk", "Aggregatieniveau","Openbaarheid.Indicatie", "Namen"],
        'facets'        : ["Aggregatieniveau", "Openbaarheid.Indicatie", "Vertrouwelijkheid.Indicatie",
                           "Vorm.GenreOfRedactie.keyword", "Classificaties.Code",
                           "Bestanden.Formaten.Datum-aanmaak", "Bestanden.Formaten.Bestandsformaat"],
        'tiles'         : ["Aggregatieniveau"],
        'charts'        : tmlo_dashboard,
        'storyboards'   : {
            'initial' : [
                    {'name'     : 'initial',
                     'layout'   : OrderedDict([
                        ('table1', [["aggregatieniveau_pie", "aggr_openbaarheid_table", "aggr_vertrouwelijkheid_table"]]),
                        ('table2', [["vorm_col", "formaat_col"]])])},
                    {'name'     : 'Bestanden',
                     'layout'   : OrderedDict([
                        ('table1', [["aanmaak_keyword_line"]]),
                        ('table2', [["vorm_omvang_col"]])])}
                ]
            },
        'filters'       : {}
        },
    }

