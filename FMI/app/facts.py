from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import collections
from collections import OrderedDict
from elasticsearch_dsl.utils import AttrList, AttrDict

import seeker
import seeker.models
import app.models as models
import app.survey as survey


def facts_survey(survey_field, facts_choices, norms_choices):
    facts_dashboard = {
        "blindcode_liking_perc_col" : {
            'chart_type': "Table",
            'chart_title' : "Candidate Liking %",
            'data_type'  : "aggr",
            'listener'    : {'select' : {'rowsort': None}},
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"},
            'Y_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics",
                'answers' : [('!', [0,'','0'])],
                'calc'    : 'percentile',
                'order'   : { "_term" : "asc" },
                },
            'options'     : {
                'sort'    : 'event',
                'frozenColumns' : 2,
                }
            },
        "blindcode_freshness_col" : {
            'chart_type': "Table",
            'chart_title' : "Candidate Freshness %",
            'data_type'   : "aggr",
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"},
            'Y_facet'     : {
                'field'   : "freshness",
                'label'   : "Freshness",
                'calc'    : 'percentile',
                },
            },
        "blindcode_emotion_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Emotion Count",
            'data_type'   : "aggr",
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"},
            'Y_facet'     : {
                'field'   : "emotion",
                'label'   : "Emotion",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                },
            },
        "blindcode_suitable_stage_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Suitable Stage Count",
            'data_type'   : "aggr",
            'X_facet'     : {
                'field'   : "blindcode.keyword",
                'label'   : "Candidate"},
            'Y_facet'     : {
                'field'   : "suitable_stage",
                'label'   : "Suitable Stage",
                'calc'    : 'percentile',
                "answers" : [],
                "values"  : ["Yes", {'v-sum':'*'}],
                'total'   : False },
            },
        }

    survey = models.SurveySeekerView()
    survey.dashboard = facts_dashboard
    survey.aggs_stack = None
    survey.aggs_stack = {}

    facets = collections.OrderedDict()
    for f in survey.facets:
        if f.field != survey.exclude:
            if f.field == "survey.keyword":
                facets[f] = [survey_field]
            else:
                facets[f] = []

    search_tile, keywords_q = survey.get_search("", facets, None, dashboard=facts_dashboard)
    search_tile = survey.get_aggr(search_tile, dashboard=facts_dashboard)

    body = search_tile.to_dict()
    #results_tile = search_tile.execute(ignore_cache=True)
    results_tile = seeker.elastic_get(self.index, '_search', search_tile.to_dict())
    tiles_select = OrderedDict()
    tiles_d = {chart_name : {} for chart_name in survey.dashboard.keys()}
    seeker.dashboard.bind_tile(survey, tiles_select, tiles_d, None, results_tile, "")

    facts = {}
    for chart_name, tile in tiles_d.items():
        chart_data = tile['All']['chart_data']
        question = survey.dashboard[chart_name]['Y_facet']['field']
        header = chart_data[0]
        for row in chart_data[1:]:
            blindcode = row[0]
            for ix in range(1, len(row)):
                answer = header[ix]
                facts[(blindcode, question, answer)] = row[ix]

    return facts



