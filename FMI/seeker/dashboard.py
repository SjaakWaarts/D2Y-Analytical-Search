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
from elasticsearch_dsl.utils import AttrList, AttrDict
from seeker.templatetags.seeker import seeker_format
from .mapping import DEFAULT_ANALYZER
import collections
import elasticsearch_dsl as dsl
import inspect
import json
import urllib
import re
import string
import numbers
from collections import OrderedDict
import pandas as pd
import numpy as np
import math
from scipy.stats import norm
import seeker.seekerview
import seeker.models
import seeker.cards as cards

#
# Google Charts and D3.JS are used to render the Chart object
# A Goolge Chart takes a DataTable as input. This DataTable is populated from the computed chart_data using
# google.visualization.arrayToDataTable.
# chart_data is a list of rows, a row on its turn is also a list. The first row describes the column headers,
# the series. The first cell of each row mentions the category.
# A column header can be a single value or a col object with an id, label, type, pattern and p (style) attribute.
# A cell can be a single value or a cell objects. Each cell has an v (value), f (formatted value) and p (stype) attribute.
# Example of a p attribute: p:{style: 'border: 1px solid green;'}
#

def answer_value_decode(answer_code):
    global qa

    answer_value = answer_code
    if answer_code == "Yes":
        answer_value = 1
    elif answer_code == "No":
        answer_value = 0
    elif type(answer_code) == str and answer_code != '':
        first_code = answer_code.split()[0]
        if first_code.isdigit():
            answer_value = int(float(first_code))
    return answer_value

#def charts_template(seekerview, charts):
#    for chart in charts:
#        if 'template' in chart:
#            source_dict = charts[chart['template']]
#            dest_dict = chart
#            stack = [("", source_dict, dest_dict)]
#            while len(stack) > 0:
#                t = stack.pop()
#                source_arg = t[0]
#                source_dict = t[1]
#                dest_dict = t[2]
#                for k, v in source_dict:
#                    if isinstance(v, dict):
#                        if k in dest_dict:
#                            stack.append(k, v, dest_dict[k])
#                        else:
#                            dest_dict[k] = v
#                    else:
#                        dest_dict[k] = v



def bind_facet(seekerview, chart, aggregations):
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    if X_field not in aggregations:
        return chart_data, meta_data

    X_label = X_facet['label']
    xfacet = seekerview.get_facet_by_field_name(X_field)
    x_total = True
    sub_total = False
    if 'total' in X_facet:
        x_total = X_facet['total']
    calc = 'count'
    if 'calc' in X_facet:
        calc = X_facet['calc']
    X_total_calc = xfacet.get_answer_total_calc(X_facet)
    if 'Y_facet' in chart:
        Y_facet = chart['Y_facet']
        Y_field = chart['Y_facet']['field']
        Y_label = Y_facet['label']
        yfacet = seekerview.get_facet_by_field_name(Y_field)
    else:
        Y_facet = None
        Y_field = ""
        Y_Label = X_label
        yfacet = None

    agg = aggregations[X_field]
    buckets = xfacet.buckets(agg)
    #categories = [X_label]
    dt_index = []
    dt_columns = [X_label]
    y_start = 1
    dt_columns.append("Total")
    y_start = y_start + 1
    if 'a-mean' in X_total_calc:
        dt_index.append('Mean')
    if 'q_mean' in X_total_calc:
        dt_columns.append('Mean')
        y_start = y_start + 1
    # next fill the series for the categories
    modes = ['sizing_', 'filling_']
    nr_respondents = 0
    total = 0
    for mode in modes:
        if mode == 'filling_':
            dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
        rownr = 0
        for X_key, bucket in buckets.items():
            # skip and map categories
            X_key = xfacet.get_answer(X_key, X_facet)
            if X_key == None:
                continue
            X_metric = xfacet.get_metric(bucket)
            if mode == 'sizing_':
                dt_index.append(X_key)
                nr_respondents = nr_respondents + X_metric
            if mode == 'filling_':
                count = X_metric
                value_code = answer_value_decode(X_key)
                if type(value_code) == int:
                    total = total + (value_code * count)
                if nr_respondents > 0:
                    percentile = count / nr_respondents
                else:
                    percentile = count
                dt.loc[X_key, X_label] = X_key
                if calc == 'percentile':
                    dt.loc[X_key, 'Total'] = dt.loc[X_key, 'Total'] + percentile * 100
                else:
                    dt.loc[X_key, 'Total'] = dt.loc[X_key, 'Total'] + count
            rownr = rownr + 1

    if calc == 'percentile':
        if nr_respondents > 0:
            mean = total / nr_respondents
        else:
            mean = total
    else:
        if rownr > 0:
            mean = nr_respondents / rownr
        else:
            mean = nr_respondents
    meta_data['mean'] = mean
    meta_data['size'] = nr_respondents
    if 'a-mean' in X_total_calc:
        x_mean = dt['Total'].mean();
        dt.loc['Mean', X_label] = 'Mean'
        dt.loc['Mean', 'Total'] = x_mean
        if X_total_calc['a-mean'] == '*':
            dt_index.remove('Mean')
            dt.drop(dt_index, axis=0, inplace=True)
        if 'q_mean' in X_total_calc:
            dt['Mean'] = pd.Series([x_mean for c in dt.index], index=dt.index)

    dt.fillna(0, inplace=True)
    # remove Total only when sub_totals exists
    if sub_total == True and x_total == False:
        dt_columns.remove('Total')
        del dt['Total']
    chart_data.append(dt_columns)
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())
    return chart_data, meta_data


def bind_aggr_result(seekerview, chart, base_dt, benchmark=None):
    chart_data = []
    meta_data = {}
    result = chart['result']
    transpose = result.get('transpose', False)
    for result_task, result_param in result.items():

        if result_task == 'top':
            dt_columns = [base_dt.columns[0]]
            dt_columns.extend(['Top {0}'.format(ix) for ix in range(1,result_param+1)])
            dt_index = list(base_dt.index)
            dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
            for cat, row in base_dt.iterrows():
                sorted_row = row[1:].sort_values(ascending=False)
                ser = base_dt.columns[0]
                dt.ix[cat, ser] = cat
                for top_ix in range(result_param):
                    ser = 'Top {0}'.format(top_ix+1)
                    dt.ix[cat, ser] = sorted_row.index[top_ix]

        if result_task == 'q-mean':
            if result_param in base_dt.columns:
                avg = base_dt[result_param].mean()
            else:
                print("bind_aggr_result: q-mean {0} not found".format(result_param))
                avg = 0
            base_dt['q-mean'] = avg
            dt_columns = list(base_dt.columns)
            dt_index = list(base_dt.index)
            dt = base_dt

        if result_task == 'lines':
            hed_lines = result_param
            dt_columns = [base_dt.columns[0]]
            dt_columns.extend([hed_line for hed_line, _ in hed_lines.items()])
            dt_index = []

            for cat in base_dt.index:
                # benchmark will be the first index/column
                if cat.strip() in benchmark:
                    dt_index.insert(0, cat.strip())
                else:
                    dt_index.append(cat.strip())
            if len(benchmark) == 0:
                dt_index.insert(0, 'Average')
            # benchmark will be the first column(s)
            if 'options' not in chart:
                chart['options'] = {}
            if transpose:
                chart['options']['frozenColumns'] = 2

            dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
            cat_total = 0
            for cat, row in base_dt.iterrows():
                dt.loc[cat, dt_columns[0]] = cat 
                sum_scores = 0
                nr_resp = 0
                hed_line_mean = None
                for hed_line, answers in hed_lines.items():
                    if 'mean' in answers:
                        hed_line_mean = hed_line
                        continue
                    col_sum = 0
                    for ix_col in range(1, len(row)):
                        answer = base_dt.columns[ix_col]
                        try:
                            answer_code = int(float(answer.split(' ')[0]))
                        except:
                            if isinstance(answer, numbers.Real):
                                answer_code = int(answer)
                            else:
                                answer_code = 0
                        if answer_code in answers:
                            col_sum = col_sum + base_dt.loc[cat, answer]
                            if answer_code > 0:
                                sum_scores = sum_scores + answer_code * base_dt.loc[cat, answer]
                                nr_resp = nr_resp + base_dt.loc[cat, answer]
                    dt.loc[cat, hed_line] = col_sum
                if nr_resp > 1:
                    Y_metric = sum_scores / nr_resp
                else:
                    Y_metric = sum_scores
                cat_total = cat_total + Y_metric
                if hed_line_mean is not None:
                    dt.loc[cat, hed_line_mean] = Y_metric
            if len(benchmark) == 0:
                dt.loc['Average', dt_columns[0]] = 'Average' 
                for ser in dt.columns[1:]:
                    sum = dt[ser].sum()
                    avg = sum / (len(dt[ser]))
                    dt.loc['Average', ser] = avg
            if ('q-mean' in result):
                if len(dt_index) == 0:
                    Y_metric= cat_total
                else:
                    Y_metric = cat_total / len(dt_index)
                Y_key = "Q-Mean"
                dt_columns.append(Y_key)
                dt.loc[dt_columns[0], Y_key] = Y_key
                rownr = 0
                for cat in dt.index:
                    dt.loc[cat, Y_key] = Y_metric
                if 'series' in chart:
                    if 'average' in chart['series']:
                        chart['series'][dt_columns.index(X_key)] = {"type": 'line'}
                        del chart['series']['average']

    chart_data.append(dt_columns)
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())
    return chart_data, meta_data

def bind_aggr(seekerview, chart, agg_name, aggregations, benchmark=None):
    chart_data = []
    meta_data = {}
    if agg_name not in aggregations:
        return chart_data, meta_data
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    X_label = X_facet['label']
    xfacet = seekerview.get_facet_by_field_name(X_field)
    x_total = True
    sub_total = False
    if 'total' in X_facet:
        x_total = X_facet['total']
    calc = 'count'
    if 'calc' in X_facet:
        calc = X_facet['calc']
    transpose = False
    if 'transpose' in chart:
        transpose = chart['transpose']
    X_total_calc = xfacet.get_answer_total_calc(X_facet)
    X_value_total_calc = xfacet.get_value_total_calc(X_facet)
    Y_total_calc = {}
    if 'Y_facet' in chart:
        Y_facet = chart['Y_facet']
        Y_field = chart['Y_facet']['field']
        Y_label = Y_facet['label']
        yfacet = seekerview.get_facet_by_field_name(Y_field)
        Y_total_calc = yfacet.get_answer_total_calc(Y_facet)
        Y_value_total_calc = yfacet.get_value_total_calc(Y_facet)
        if 'calc' in Y_facet:
            calc = Y_facet['calc']
    else:
        Y_facet = None
        Y_field = ""
        Y_Label = X_label
        yfacet = None
    # Aggregation is an AttrDict
    # Buckets is an AttrList for Terms and AttrDict for Keywords. The facet.buckets method returns alwasy a OrderedDict
    # Bucket is an AttrDict and can act as a Sub-Aggregation
    agg = aggregations[agg_name]
    buckets = xfacet.buckets(agg)
    dt_index = []
    categories = []
    dt_columns = [X_label]
    series = []
    y_start = 1
    dt_columns.append("Total")
    y_start = y_start + 1
    if 'q-mean' in X_total_calc:
        dt_index.append('Mean')
    # ONLY X FACET
    if Y_field == "":
        if 'a-mean' in X_total_calc:
            dt_index.append('Mean')
            if X_total_calc['a-mean'] == '**':
                dt_columns.append('q-Mean')
                y_start = y_start + 1
    else:
        if 'a-mean' in Y_total_calc:
            dt_columns.append('Mean')
            y_start = y_start + 1
            if Y_total_calc['a-mean'] == '**':
                dt_columns.append('q-Mean')
                y_start = y_start + 1
        if 'a-wmean' in Y_total_calc:
            dt_columns.append('Mean')
            y_start = y_start + 1
            if Y_total_calc['a-wmean'] == '**':
                dt_columns.append('q-Mean')
                y_start = y_start + 1
    # next fill the series for the categories
    nr_respondents = 0
    modes = ['sizing_', 'filling_']
    for mode in modes:
        if mode == 'filling_':
            # benchmark will be the first column(s)
            if 'options' not in chart:
                chart['options'] = {}
            chart['options']['frozenColumns'] = 1
            if len(benchmark) > 0:
                if not transpose:
                    if benchmark[0] in dt_columns:
                        ix = dt_columns.index(benchmark[0])
                        dt_columns.insert(1, dt_columns.pop(ix))
                        chart['options']['frozenColumns'] = 2
                else:
                    if benchmark[0] in dt_index:
                        ix = dt_index.index(benchmark[0])
                        dt_index.insert(0, dt_index.pop(ix))
                        chart['options']['frozenColumns'] = 2
            if x_total:
                chart['options']['frozenColumns'] = chart['options']['frozenColumns'] + 1
            dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
        X_rownr = 0
        X_count = 0
        X_total = 0
        rownr = 0
        for X_key, bucket in buckets.items():
            # skip and map categories
            X_key = xfacet.get_answer(X_key, X_facet)
            if X_key == None:
                continue
            X_metric = xfacet.get_metric(bucket)
            X_code = answer_value_decode(X_key)
            X_rownr = X_rownr + 1
            X_count = X_count + X_metric
            if type(X_code) == int:
                X_total = X_total + (X_metric * X_code)
            if mode == 'sizing_':
                dt_index.append(X_key)
                categories.append(X_key)
                nr_respondents = nr_respondents + X_metric
            if mode == 'filling_':
                dt.loc[X_key, X_label] = str(X_key)
                count = X_metric
                if nr_respondents > 0:
                    percentile = count / nr_respondents
                else:
                    percentile = count
                if calc == 'percentile':
                    dt.loc[X_key, "Total"] = percentile * 100
                else:
                    dt.loc[X_key, "Total"] = count
                total = 0
            # loop through the different values for this category, normally only one
            xvalbuckets = xfacet.valbuckets(bucket)
            X_value_rownr = 0
            X_value_count = 0
            X_value_total = 0
            # ONLY X FACET
            if Y_field == "":
                for X_value_key, xvalbucket in xvalbuckets.items():
                    # skip and map values
                    X_value_key = xfacet.get_value_key(X_value_key, X_facet)
                    if X_value_key == None:
                        continue
                    # no values exist
                    if X_value_key == 'Total':
                        X_metric = nr_respondents
                    X_value_metric = xfacet.get_metric(xvalbucket)
                    X_value_code = answer_value_decode(X_value_key)
                    X_value_rownr = X_value_rownr + 1
                    X_value_count = X_value_count + X_value_metric
                    if type(X_value_code) == int:
                        X_value_total = X_value_total + (X_value_metric * X_value_code)
                    if 'layout' in X_value_total_calc:
                        if X_value_total_calc['layout'] == 'series':
                            if mode == 'sizing_':
                                sub_total = True
                                if X_value_key not in dt_columns:
                                    dt_columns.append(str(X_value_key))
                                    series.append(str(X_value_key))
                            if mode == 'filling_':
                                count = X_value_metric
                                if X_metric > 0:
                                    percentile = count / X_metric
                                else:
                                    percentile = count
                                if calc == 'percentile':
                                    dt.loc[X_key, X_value_key] = percentile * 100
                                else:
                                    dt.loc[X_key, X_value_key] = count
                        if X_value_total_calc['layout'] == 'categories':
                            if mode == 'sizing_':
                                if X_value_key not in dt_index:
                                    dt_index.append(str(X_value_key))
                                    categories.append(str(X_value_key))
                            if mode == 'filling_':
                                dt.loc[X_value_key, X_label] = str(X_value_key)
                                count = X_value_metric
                                if X_metric > 0:
                                    percentile = count / X_metric
                                else:
                                    percentile = count
                                if calc == 'percentile':
                                    dt.loc[X_value_key, 'Total'] = percentile * 100
                                else:
                                    dt.loc[X_value_key, 'Total'] = count
                if any(aggr in X_value_total_calc for aggr in ['v-sum','v-mean']):
                    if mode == 'filling_':
                        count = X_value_count
                        if X_metric > 0:
                            percentile = count / X_metric
                        else:
                            percentile = count
                        if calc == 'percentile':
                            dt.loc[X_key, "Total"] = percentile * 100
                        else:
                            dt.loc[X_key, "Total"] = count
            # X FACET AND Y FACET
            if Y_field != "":
                for X_value_key, xvalbucket in xvalbuckets.items():
                    # skip and map values
                    X_value_key = xfacet.get_value_key(X_value_key, X_facet)
                    if X_value_key == None:
                        continue
                    X_value_metric = xfacet.get_metric(xvalbucket)
                    X_value_code = answer_value_decode(X_value_key)
                    X_value_rownr = X_value_rownr + 1
                    X_value_count = X_value_count + X_value_metric
                    if type(X_value_code) == int:
                        X_value_total = X_value_total + (X_value_metric * X_value_code)
                    if Y_field in xvalbucket:
                        subagg = xvalbucket[Y_field]
                        subbuckets = yfacet.buckets(subagg)
                        Y_rownr = 0
                        Y_count = 0
                        Y_total = 0
                        for Y_key, subbucket in subbuckets.items():
                            # skip and map answers, categories
                            Y_key = yfacet.get_answer(Y_key, Y_facet)
                            if Y_key == None:
                                continue
                            sub_total = True
                            Y_metric = yfacet.get_metric(subbucket)
                            # check whether Y facet has subbuckets (multiple values)
                            # loop through the different values for this category, normally only one
                            # for metric facets there are no subbuckets
                            yvalbuckets = yfacet.valbuckets(subbucket)
                            if len(yvalbuckets) == 0:
                                Y_value_count = Y_metric
                                Y_value_total = Y_metric
                            else:
                                Y_value_count = 0
                                Y_value_total = 0
                            Y_value_rownr = 0
                            Y_code = answer_value_decode(Y_key)
                            for Y_value_key, yvalbucket in yvalbuckets.items():
                                # skip and map values
                                Y_value_key = yfacet.get_value_key(Y_value_key, Y_facet)
                                if Y_value_key is None:
                                    continue
                                if yvalbucket is None:
                                    continue
                                V_metric = yfacet.get_metric(yvalbucket)
                                Y_value_code = answer_value_decode(Y_value_key)
                                Y_value_rownr = Y_value_rownr + 1
                                Y_value_count = Y_value_count + V_metric
                                if type(Y_value_code) == int:
                                    Y_value_total = Y_value_total + (V_metric * Y_value_code)
                                if 'layout' in Y_value_total_calc:
                                    if Y_value_total_calc['layout'] == 'series':
                                        if mode == 'sizing_':
                                            if Y_value_key not in dt_columns:
                                                series.append(Y_value_key)
                                                inserted = False
                                                for i in range(y_start, len(dt_columns)):
                                                    if Y_key < dt_columns[i]:
                                                        dt_columns.insert(i, Y_value_key)
                                                        inserted = True
                                                        break
                                                if not inserted:
                                                    dt_columns.append(Y_value_key)
                                        if mode == 'filling_':
                                            count = V_metric
                                            if Y_metric > 0:
                                                percentile = count / Y_metric
                                            else:
                                                percentile = count
                                            if calc == 'percentile':
                                                dt.loc[X_key, Y_value_key] = percentile * 100
                                            else:
                                                dt.loc[X_key, Y_value_key] = count
                            if any(aggr in Y_value_total_calc for aggr in ['v-sum','v-mean']):
                                if mode == 'sizing_':
                                    if Y_key not in dt_columns:
                                        series.append(Y_key)
                                        inserted = False
                                        for i in range(y_start, len(dt_columns)):
                                            if Y_key < dt_columns[i]:
                                                dt_columns.insert(i, Y_key)
                                                inserted = True
                                                break
                                        if not inserted:
                                            dt_columns.append(Y_key)
                                if mode == 'filling_':
                                    count = Y_value_count
                                    if type(Y_code) == int:
                                        total = total + (Y_code * count)
                                    if X_metric > 0:
                                        percentile = count / X_metric
                                    else:
                                        percentile = count
                                    if calc == 'percentile':
                                        dt.loc[X_key, Y_key] = percentile * 100
                                    else:
                                        dt.loc[X_key, Y_key] = count
                            Y_rownr + Y_rownr + 1
                            Y_count = Y_count + Y_value_count
                            if type(Y_code) == int:
                                Y_total = Y_total + (Y_code * Y_value_count)
                if mode == 'filling_':
                    if any(aggr in Y_total_calc for aggr in ['a-sum','a-mean','a-wmean']):
                        if 'a-sum' in Y_total_calc:
                            dt.loc[X_key, 'Mean'] =  Y_count
                        if 'a-mean' in Y_total_calc:
                            if Y_rownr > 0:
                                dt.loc[X_key, 'Mean'] =  Y_count / Y_rownr
                            else:
                                dt.loc[X_key, 'Mean'] =  Y_count
                        if 'a-wmean' in Y_total_calc:
                            if Y_count > 0:
                                dt.loc[X_key, 'Mean'] =  Y_total / Y_count
                            else:
                                dt.loc[X_key, 'Mean'] =  Y_total
            rownr = rownr + 1

    if 'q-mean' in X_total_calc:
        for col in dt_columns[1:]:
            xq_mean = dt[col].mean();
            dt.loc['Mean', X_label] = 'Mean'
            dt.loc['Mean', col] = xa_mean
        if X_total_calc['q-mean'] == '*':
            dt.drop(categories, axis=0, inplace=True)
            dt_index = list(dt.index)
    if calc == 'percentile':
        if nr_respondents > 0:
            mean = X_total / nr_respondents
        else:
            mean = X_total
    else:
        if X_rownr > 0:
            mean = nr_respondents / X_rownr
        else:
            mean = nr_respondents
    meta_data['mean'] = mean
    meta_data['size'] = nr_respondents
    # ONLY X FACET
    if Y_field == "":
        if 'a-mean' in X_total_calc:
            x_mean = dt['Total'].mean();
            dt.loc['Mean', X_label] = 'Mean'
            dt.loc['Mean', 'Total'] = x_mean
            if X_total_calc['a-mean'] == '*':
                dt_index.remove('Mean')
                dt.drop(dt_index, axis=0, inplace=True)
            if X_total_calc['a-mean'] == '**':
                q_mean = dt['Mean'].mean();
                dt['q-Mean'] = pd.Series([q_mean for c in dt.index], index=dt.index)
    else:
        if 'a-mean' in Y_total_calc:
            for cat in dt_index:
                a_mean = dt.ix[cat][series].mean();
                dt.loc[cat, 'Mean'] = a_mean
            if Y_total_calc['a-mean'][0] == '*':
                dt.drop(series, axis=1, inplace=True)
                dt_columns = list(dt.columns)
            if Y_total_calc['a-mean'] == '**':
                q_mean = dt['Mean'].mean();
                dt['q-Mean'] = pd.Series([q_mean for c in dt.index], index=dt.index)
        if 'a-wmean' in Y_total_calc:
            #for cat in dt_index:
            #    a_mean = dt.ix[cat][series].mean();
            #    dt.loc[cat, 'Mean'] = a_mean
            if Y_total_calc['a-wmean'][0] == '*':
                dt.drop(series, axis=1, inplace=True)
                dt_columns = list(dt.columns)
            if Y_total_calc['a-wmean'] == '**':
                q_mean = dt['Mean'].mean();
                dt['q-Mean'] = pd.Series([q_mean for c in dt.index], index=dt.index)

    dt.fillna(0, inplace=True)
    if sub_total == True and x_total == False and 'Total' in dt_columns:
        dt_columns.remove('Total')
        del dt['Total']

    if transpose:
        # first column contains the labels, remove this column before transpose and add it again after transpose
        del dt[X_label]
        dt = dt.transpose()
        dt_trans_columns = [Y_label]
        dt_trans_columns.extend(dt_index)
        dt_trans_index = dt_columns[1:]
        dt.insert(0, Y_label, dt_trans_index)
        dt_columns = dt_trans_columns

    if 'result' in chart:
        chart_data, meata_data = bind_aggr_result(seekerview, chart, dt, benchmark=benchmark)
    else:
        chart_data.append(dt_columns)
        for ix, row in dt.iterrows():
            chart_data.append(row.tolist())
    return chart_data, meta_data

def bind_topline_aggr(seekerview, chart, aggr_name, aggregations, benchmark=None):
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    X_label = X_facet['label']
    Y_facet = chart['Y_facet']
    Y_field = Y_facet['field']
    Y_label = Y_facet['label']
    if 'lines' in X_facet:
        hed_lines = X_facet['lines'][X_field]
    else:
        hed_lines = Y_facet['lines'][Y_field]
    data, meta_data = bind_aggr(seekerview, chart, aggr_name, aggregations, benchmark)
    if len(data) == 0:
        return

    dt_index = []
    dt_columns = [X_label]
    for col in data[0][1:]:
        if col == 'Total':
            continue
        blindcode = col.strip()
        # benchmark will be the first column(s)
        if blindcode in benchmark:
            dt_columns.insert(1, blindcode)
        else:
            dt_columns.append(blindcode)
    if len(benchmark) == 0:
        dt_columns.insert(1, 'Average')

    # benchmark will be the first column(s)
    if 'options' not in chart:
        chart['options'] = {}
    chart['options']['frozenColumns'] = 2

    dt_index = list(hed_lines.keys())
    dt_index.sort()
    dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
    dt[X_label] = dt_index


    # scan through the rows to populate df
    Y_total = 0
    hit_count = 0
    Y_benchmark = 0
    benchmark_count = 0
    cand_topline = {}

    for ix in range(1, len(data[0])):
        blindcode = data[0][ix].strip()
        if blindcode == 'Total':
            continue
        sum_scores = 0
        nr_resp = 0
        for row in data[1:]:
            answer = row[0]
            try:
                answer_code = int(float(answer.split(' ')[0]))
            except:
                if isinstance(answer, numbers.Real):
                    answer_code = int(answer)
                else:
                    answer_code = 0
            for hed_line, answers in hed_lines.items():
                if answer_code in answers:
                    dt.loc[hed_line, blindcode] = dt.loc[hed_line, blindcode] + row[ix]
            if answer_code > 0:
                sum_scores = sum_scores + answer_code * row[ix]
                nr_resp = nr_resp + row[ix]
        for hed_line, answers in hed_lines.items():
            if 'mean' in answers:
                if nr_resp > 1:
                    Y_metric = sum_scores / nr_resp
                else:
                    Y_metric = sum_scores
                dt.loc[hed_line, blindcode] = Y_metric
                Y_total = Y_total + Y_metric
                hit_count = hit_count + 1

    if len(benchmark) == 0:
        for hed in dt.index:
            sum = dt.ix[hed][1:].sum()
            avg = sum / (len(dt._ix[hed]) - 2)
            dt.loc[hed, 'Average'] = avg
    if ('q-mean' in X_facet):
        if hit_count == 0:
            Y_metric= Y_total
        else:
            Y_metric = Y_total / hit_count
        X_key = "Q-Mean"
        dt_index.append(X_key)
        dt.loc[X_key, X_label] = X_key
        rownr = 0
        for colnr in range(1, len(dt_columns)):
            dt.loc[X_key, dt_columns[colnr]] = Y_metric
        if 'series' in chart:
            if 'average' in chart['series']:
                chart['series'][dt_columns.index(X_key)] = {"type": 'line'}
                del chart['series']['average']

    # prepare for the setProperty formatter. Capture the cells for which a win95, win90, win80, lose95, lose90, lose80
    # className have to be set. This win/lose is set based on the first columns, which contains either the benchmark
    # or the average.
    # The cells in a DataTable start at rownr 0 (this not the header) and at colnr 0 (this is the label)
    if 'formatter' in chart and len(dt.columns) > 1:
        if 'setProperty' in chart['formatter']:
            winlose = []
            for rownr in range(0, len(dt)):
                line = dt.ix[rownr]
                avg = line[1]
                var = 0
                for colnr in range(2, len(line)):
                    var = var + abs(line[colnr] - avg)
                stddev = math.sqrt(var)
                int95 = norm.interval(0.95, avg, stddev)
                int90 = norm.interval(0.90, avg, stddev)
                int80 = norm.interval(0.80, avg, stddev)
                winlose.append([rownr, 1, 'className', 'benchmark'])
                for colnr in range(2, len(line)):
                    if line[colnr] >= int95[1]:
                        winlose.append([rownr, colnr, 'className', 'win95'])
                    elif line[colnr] >= int90[1]:
                        winlose.append([rownr, colnr, 'className', 'win90'])
                    elif line[colnr] >= int80[1]:
                        winlose.append([rownr, colnr, 'className', 'win80'])
                    elif line[colnr] <=int95[0]:
                        winlose.append([rownr, colnr, 'className', 'lose95'])
                    elif line[colnr] <=int90[0]:
                        winlose.append([rownr, colnr, 'className', 'lose90'])
                    elif line[colnr] <=int80[0]:
                        winlose.append([rownr, colnr, 'className', 'lose80'])
            chart['formatter']['setProperty'] = winlose

    transpose = False
    if 'transpose' in chart:
        transpose = chart['transpose']
    if transpose:
        # first column contains the labels, remove this column before transpose and add it again after transpose
        del dt[X_label]
        dt = dt.transpose()
        dt_trans_columns = [Y_label]
        dt_trans_columns.extend(dt_index)
        dt_trans_index = dt_columns[1:]
        dt.insert(0, Y_label, dt_trans_index)
        dt_columns = dt_trans_columns

    dt.fillna(0, inplace=True)
    chart_data.append(dt_columns)
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())
    return chart_data, meta_data


def bind_hits(seekerview, chart, hits, benchmark=None):
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    X_label = X_facet['label']
    xfacet = seekerview.get_facet_by_field_name(X_field)
    x_total = True
    if 'total' in X_facet:
        x_total = X_facet['total']
    if 'Y_facet' in chart:
        Y_facet = chart['Y_facet']
        Y_field = Y_facet['field']
        Y_label = Y_facet['label']
        yfacet = seekerview.get_facet_by_field_name(Y_field)
    else:
        Y_facet = None
        Y_field = None
        Y_Label = X_label
        yfacet = None

    # next fill the series for the categories
    Y_total = 0
    hit_count = 0
    Y_benchmark = 0
    benchmark_count = 0
    dt_index = []
    dt_columns = [X_label]
    if x_total:
        dt_columns.append("Total")
    dt = pd.DataFrame(0.0, columns=dt_columns, index=[0])
    rownr = 0
    for hit in hits:
        X_key = hit['_source'][X_field]
        # only process new X keys
        if X_key in dt_index:
            continue
        dt.loc[rownr, X_label] = X_key
        dt_index.append(X_key)
        #if x_total:
        #    series[1] = 1
        Y_metric = 0
        if Y_facet and Y_field in hit['_source']:
            Y_key = hit['_source'][Y_field]
            if type(Y_key) == list:
                Y_key_nested = Y_key
                Y_nested = 0
                nested_count = 0
                for Y_value in Y_key_nested:
                    Y_key = Y_value['val']
                    Y_metric = Y_value[Y_facet['metric']]
                    if 'answers' in Y_facet:
                        # in case anaswers is empty, add all y values
                        if Y_value['val'] in Y_facet['answers'] or len( Y_facet['answers']) == 0:
                            Y_nested = Y_nested + Y_metric
                            nested_count = nested_count + 1
                            Y_key = yfacet.decoder(X_key, Y_key)
                            if type(Y_key) == int:
                                Y_key = "{0:d}".format(Y_key)
                            #series[categories.index(Y_key)] = Y_metric
                            if Y_key not in dt_columns:
                                dt_columns.append(Y_key)
                            dt.loc[rownr, Y_key] = Y_metric
                    else:
                        # in case the answer is scaled, starts with a number, use weight factor for average
                        try:
                            weight = int(float(Y_key.split(' ')[0]))
                        except:
                            weight = 1
                        Y_nested = Y_nested + Y_metric * weight
                        nested_count = nested_count + 1
                if nested_count == 0:
                    Y_metric= Y_nested
                else:
                    Y_metric = Y_nested / nested_count
                if 'answers' not in Y_facet:
                    Y_key = Y_facet['label']
                    #series[categories.index(Y_key)] = Y_metric
                    dt.loc[rownr, Y_key] = Y_metric
                    if Y_key not in dt_columns:
                        dt_columns.append(Y_key)
                elif 'a-mean' in Y_facet:
                    if Y_facet['a-mean'] == True:
                        Y_key = "A-Mean"
                        #series[categories.index(Y_key)] = Y_metric
                        dt.loc[rownr, Y_key] = Y_metric
                        if Y_key not in dt_columns:
                            dt_columns.append(Y_key)
                        if 'series' in chart:
                            if 'average' in chart['series']:
                                chart['series'][dt_columns.index(Y_key)] = {"type": 'line'}
                                del chart['series']['average']
            else:
                if type(Y_key) == str:
                    try:
                        Y_metric = float(Y_key.split(' ')[0])
                    except:
                        Y_metric = 0
                else:
                    Y_metric = hit['_source'][Y_field]
                Y_key = Y_facet['label']
                #series[categories.index(Y_key)] = Y_metric
                dt.loc[rownr, Y_key] = Y_metric
                if Y_key not in dt_columns:
                    dt_columns.append(Y_key)
        Y_total = Y_total + Y_metric
        hit_count = hit_count + 1
        if X_key in benchmark:
            Y_benchmark = Y_benchmark + Y_metric
            benchmark_count = benchmark_count + 1
        #chart_data.append(series)
        rownr = rownr + 1
    if ('q-mean' in Y_facet):
        if hit_count == 0:
            Y_metric= Y_total
        else:
            Y_metric = Y_total / hit_count
        Y_key = "Q-Mean"
        rownr = 0
        #for series in chart_data['data']:
        #    series[categories.index(Y_key)] = Y_metric
        for rownr in range(0, len(dt)):
            dt.loc[rownr, Y_key] = Y_metric
            if Y_key not in dt_columns:
                dt_columns.append(Y_key)
            rownr = rownr + 1
        if 'series' in chart:
            if 'average' in chart['series']:
                chart['series'][dt_columns.index(Y_key)] = {"type": 'line'}
                del chart['series']['average']
    if len(benchmark) > 0:
        if benchmark_count == 0:
            Y_metric= Y_benchmark
        else:
            Y_metric = Y_benchmark / benchmark_count
        Y_key = "Benchmark"
        rownr = 0
        #for series in chart_data['data']:
        #    series[categories.index(Y_key)] = Y_metric
        for rownr in range(0, len(dt)):
            dt.loc[rownr, Y_key] = Y_metric
            if Y_key not in dt_columns:
                dt_columns.append(Y_key)
            rownr = rownr + 1
        # replace average and benchmark for combobox with real position
        if 'series' in chart:
            if 'series' in chart:
                if 'benchmark' in chart['series']:
                    chart['series'][categories.index(Y_key)] = {"type": 'line'}
                    del chart['series']['benchmark']

    #if len(chart_data) > 0:
    #    chart_data.insert(0, categories)
    transpose = False
    if 'transpose' in chart:
        transpose = chart['transpose']
    if transpose:
        # first column contains the labels, remove this column before transpose and add it again after transpose
        del dt[X_label]
        dt = dt.transpose()
        dt_trans_columns = [Y_label]
        dt_trans_columns.extend(dt_index)
        dt_trans_index = dt_columns[1:]
        dt.insert(0, Y_label, dt_trans_index)
        dt_columns = dt_trans_columns

    dt.fillna(0, inplace=True)
    chart_data.append(dt_columns)
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())
    return chart_data, meta_data

def _nested_box(nestedlist, values):
    prc = 0
    for item in nestedlist:
        try:
            item_code = int(float(item['val'].split(' ')[0]))
        except:
            item_code = item['val']
        for value in values:
            if item_code == value:
                prc = prc + item['prc']
    return prc

def _nested_mean(nestedlist):
    prc = 0
    if len(nestedlist) > 0:
        for item in nestedlist:
            try:
                weight = int(float(item['val'].split(' ')[0]))
            except:
                weight = 1
            prc = prc + item['prc'] * weight
        prc = prc / len(nestedlist)
    return prc


def bind_topline(seekerview, chart, hits, benchmark=None):
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_fields = X_facet['fields']
    Y_facet = chart['Y_facet']
    Y_field = Y_facet['field']

    topline_columns = []
    for hit in hits:
        blindcode = hit['_source'][Y_field]
        # benchmark will be the first column(s)
        if blindcode in benchmark:
            topline_columns.insert(0, blindcode)
        else:
            topline_columns.append(blindcode)
    topline_index = ['Hedonics Mean', 'Hedonics Excellent', 'Hedonics Top2', 'Hedonics Top3', 'Hedonics Bottom2']
    topline_df = pd.DataFrame(0.0, columns=topline_columns, index=topline_index)

    # scan through the hits to populate df
    Y_total = 0
    hit_count = 0
    Y_benchmark = 0
    benchmark_count = 0
    cand_topline = {}
    for hit in hits:
        blindcode = hit['_source'][Y_field]
        if 'liking' in hit['_source']:
            hedonics = hit['_source']['liking']
        else:
            hedonics = []
        Y_nested = _nested_mean(hedonics)
        topline_df.loc['Hedonics Mean', blindcode] = Y_nested
        topline_df.loc['Hedonics Excellent', blindcode] = _nested_box(hedonics, [7])
        topline_df.loc['Hedonics Top2', blindcode] = _nested_box(hedonics, [7, 6])
        topline_df.loc['Hedonics Top3', blindcode] = _nested_box(hedonics, [7, 6, 5])
        topline_df.loc['Hedonics Bottom2', blindcode] = _nested_box(hedonics, [2, 1])
        Y_total = Y_total + Y_nested
        hit_count = hit_count + 1

    for ix in topline_df.index:
        series = [ix]
        series.extend(topline_df.ix[ix].tolist())
        chart_data.append(series)

    if len(chart_data) > 0:
        categories = ['Questions']
        categories.extend(topline_columns)
        chart_data.insert(0, categories)
    return chart_data, meta_data


def bind_correlation(seekerview, chart, stats_df):
    # The data will be loaded in google_chart arrayToDataTable format
    # This means columns=series and rows=categories.
    # First Row are the column=series headers, followed by the different categories
    # First Column are the category names followed by the serie values
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    # First row
    row = [X_facet['label']['category']]
    for col in X_facet['stats']:
        if col in stats_df.columns:
            if col in X_facet['label']:
                row.append(X_facet['label'][col])
            else:
                row.append(col)
    chart_data.append(row)
    # Category rows
    for ix, stats_s in stats_df.iterrows():
        # First column
        row = [ix[0]]
        for col in X_facet['stats']:
            # Series columns
            if col in stats_df.columns:
                row.append(stats_s[col])
        chart_data.append(row)
    return chart_data, meta_data


def bind_chart(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark):
    chart_data = []
    meta_data = {}
    data_type = chart['data_type']
    X_facet = chart['X_facet']
    if data_type == 'facet':
        chart_data, meta_data = bind_facet(seekerview, chart, aggregations)
    elif data_type == 'aggr':
        if 'base' in chart:
            if facet_tile_value == 'All':
                aggr_name = chart['base']
            else:
                aggr_name = chart['X_facet']['field']
            chart_data, meta_data = bind_topline_aggr(seekerview, chart, aggr_name, aggregations, benchmark)
        else:
            if facet_tile_value == 'All':
                aggr_name = chart_name
            else:
                aggr_name = chart['X_facet']['field']
            chart_data, meta_data = bind_aggr(seekerview, chart, aggr_name, aggregations, benchmark)
    elif data_type == 'hits':
        chart_data, meta_data = bind_hits(seekerview, chart, hits, benchmark)
    elif data_type == 'topline':
        chart_data, meta_data = bind_topline(seekerview, chart, hits, benchmark)
    elif data_type[0:4] == 'card':
        chart_data, meta_data = cards.bind_card(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark)
    return chart_data, meta_data

def bind_tile(seekerview, tiles_select, tiles_d, facets_tile, results, benchmark):
    #hits = getattr(results, 'hits', AttrList([]))
    #aggregations = getattr(results, 'aggregations', AttrDict([]))
    hits = results.get('hits', {}).get('hits', [])
    aggregations = results.get('aggregations', {})

    if facets_tile == None:
        tiles_select['All'] = ['All']
    else:
        for facet_tile in facets_tile:
            tiles_select[facet_tile.label] = []

    for chart_name, chart in seekerview.dashboard.items():
    #for chart_name, chart in charts.items():
        data_type = chart['data_type']
        if data_type == 'correlation':
            continue
        if data_type == 'join':
            continue
        X_facet = chart['X_facet']
        if facets_tile == None:
            chart_data, meta_data = bind_chart(seekerview, chart_name, chart, hits, aggregations, 'All', benchmark)
            tiles_d[chart_name]['All'] = {'chart_data' : chart_data, 'meta_data' : meta_data}
        else:
            for facet_tile in facets_tile:
                if 'base' in chart:
                    aggr_name = chart['base']
                else:
                    aggr_name = chart_name
                tile_aggr_name = facet_tile.name + '_' + aggr_name
                tiles = {}
                if tile_aggr_name in aggregations:
                    tile_aggr = aggregations[tile_aggr_name]
                    tiles = facet_tile.buckets(tile_aggr)

                for facet_tile_value, tile in tiles.items():
                    if facet_tile_value not in tiles_select[facet_tile.label]:
                        tiles_select[facet_tile.label].append(facet_tile_value)
                    chart_data, meta_data = bind_chart(seekerview, chart_name, chart, hits, tile, facet_tile_value, benchmark)
                    tiles_d[chart_name][facet_tile_value] = {'chart_data' : chart_data, 'meta_data' : meta_data}
    return


def bind_nestedfield(seekerview, chart, hit, benchmark):
    chart_data = []
    meta_data = {}
    X_facet = chart['X_facet']
    X_field = X_facet['field']
    if X_field not in hit['_source']:
        return chart_data, meta_data

    X_label = X_facet['label']
    xfacet = seekerview.get_facet_by_field_name(X_field)
    x_total = True
    sub_total = False
    if 'total' in X_facet:
        x_total = X_facet['total']
    calc = 'count'
    if 'calc' in X_facet:
        calc = X_facet['calc']
    X_total_calc = xfacet.get_answer_total_calc(X_facet)
    if 'Y_facet' in chart:
        Y_facet = chart['Y_facet']
        Y_field = chart['Y_facet']['field']
        Y_label = Y_facet['label']
        yfacet = seekerview.get_facet_by_field_name(Y_field)
    else:
        Y_facet = None
        Y_field = ""
        Y_Label = X_label
        yfacet = None

    nestedfield_values = hit['_source'][X_field]
    #categories = [X_label]
    dt_index = []
    dt_columns = [X_label]
    y_start = 1
    dt_columns.append("Total")
    y_start = y_start + 1
    if 'a-mean' in X_total_calc:
        dt_index.append('Mean')
    if 'q_mean' in X_total_calc:
        dt_columns.append('Mean')
        y_start = y_start + 1
    # next fill the series for the categories
    modes = ['sizing_', 'filling_']
    nr_respondents = 0
    total = 0
    for mode in modes:
        if mode == 'filling_':
            dt = pd.DataFrame(0.0, columns=dt_columns, index=dt_index)
        rownr = 0
        #for X_key, bucket in buckets.items():
        for nestedfield_value in nestedfield_values:
            # skip and map categories
            X_key = nestedfield_value['val']
            X_key = xfacet.get_answer(X_key, X_facet)
            if X_key == None:
                continue
            X_metric = nestedfield_value['prc']
            if mode == 'sizing_':
                dt_index.append(X_key)
                nr_respondents = nr_respondents + 1
                total = total + X_metric
            if mode == 'filling_':
                count = X_metric
                value_code = answer_value_decode(X_key)
                if type(value_code) == int:
                    total = total + (value_code * count)
                if nr_respondents > 0:
                    percentile = count / nr_respondents
                else:
                    percentile = count
                dt.loc[X_key, X_label] = X_key
                if calc == 'percentile':
                    dt.loc[X_key, 'Total'] = dt.loc[X_key, 'Total'] + percentile * 100
                else:
                    dt.loc[X_key, 'Total'] = dt.loc[X_key, 'Total'] + count
            rownr = rownr + 1

    if calc == 'percentile':
        if nr_respondents > 0:
            mean = total / nr_respondents
        else:
            mean = total
    else:
        if rownr > 0:
            mean = nr_respondents / rownr
        else:
            mean = nr_respondents
    meta_data['mean'] = mean
    meta_data['size'] = nr_respondents
    if 'a-mean' in X_total_calc:
        x_mean = dt['Total'].mean();
        dt.loc['Mean', X_label] = 'Mean'
        dt.loc['Mean', 'Total'] = x_mean
        if X_total_calc['a-mean'] == '*':
            dt_index.remove('Mean')
            dt.drop(dt_index, axis=0, inplace=True)
        if 'q_mean' in X_total_calc:
            dt['Mean'] = pd.Series([x_mean for c in dt.index], index=dt.index)

    dt.fillna(0, inplace=True)
    # remove Total only when sub_totals exists
    if sub_total == True and x_total == False:
        dt_columns.remove('Total')
        del dt['Total']
    if nr_respondents > 0:
        chart_data.append(dt_columns)
        for ix, row in dt.iterrows():
            chart_data.append(row.tolist())
    return chart_data, meta_data

def bind_minichart(seekerview, tiles_d, chart_name, chart, hits, benchmark):
    data_type = chart['data_type']
    tiles_d[chart_name] = {}
    for hit in hits:
        if data_type == 'nestedfield':
            chart_data, meta_data = bind_nestedfield(seekerview, chart, hit, benchmark)
        elif data_type == 'optionfield':
            chart_data, meta_data = bind_optionfield(seekerview, chart, hit, benchmark)
        elif data_type == 'innerhits':
            chart_data, meta_data = bind_innerhits(seekerview, chart, hit, benchmark)
        tiles_d[chart_name][hit['_id']] = {'chart_data' : chart_data, 'meta_data' : meta_data}

def bind_minicharts(seekerview, tiles_d, results, benchmark):
    hits = results.get('hits', {}).get('hits', [])
    aggregations = results.get('aggregations', {})
    for chart_name, chart in seekerview.minicharts.items():
        bind_minichart(seekerview, tiles_d, chart_name, chart, hits, benchmark)


def get_fqa_v_respondents(fqav_df, question, answer, facet):
    values = []
    nr_respondents = 0
    for column in fqav_df.columns:
        if column[0] == question and column[1] == answer:
            values.append(column[2])
            nr_respondents = nr_respondents + fqav_df[column][facet]
    return values, nr_respondents

def get_fq_av_respondents(fqav_df, question, facet):
    answers = []
    values = []
    nr_respondents = 0
    for column in fqav_df.columns:
        if column[0] == question:
            answers.append(column[1])
            values.append(column[2])
            nr_respondents = nr_respondents + fqav_df[column][facet]
    return answers, values, nr_respondents

def fill_tile_df(seekerview, tiles_d, base_charts):
    tile_df = pd.DataFrame(columns=('facet_tile', 'chart_name', 'q_field', 'x_field', 'y_field', 'metric'))
    rownr = 0
    for chart_name, facets in tiles_d.items():
        if chart_name in base_charts:
            chart = seekerview.dashboard[chart_name]
            for facet_value, data in facets.items():
                if facet_value == 'All':
                    continue
                chart_data = data['chart_data']
                X_facet = chart['X_facet']
                X_field = X_facet['field']
                if len(chart_data) > 0:
                    categories = chart_data[0]
                    q_field = X_field
                    rownr = len(tile_df)
                    for series in chart_data[1:]:
                        x_field = series[0]
                        for ix in range(1, len(categories)):
                            y_field = categories[ix]
                            metric = series[ix]
                            tile_df.loc[rownr] = [facet_value, chart_name, q_field, x_field, y_field, metric]
                            rownr = rownr + 1
    return tile_df

def stats(seekerview, chart_name, tiles_d):
    chart = seekerview.dashboard[chart_name]
    base_charts = chart['base']
    #questions = tile_df['q_field']
    stats_df = pd.DataFrame()
    tile_df = fill_tile_df(seekerview, tiles_d, base_charts)

    facets = tile_df['facet_tile']
    f_index = np.unique(facets).tolist()
    chart_names = []
    qav_q_columns = []
    qav_a_columns = []
    qav_av_columns = []
    qa_q_columns = []
    qa_a_columns = []
    #tile_df = tile_df[tile_df['y_field'] != 'Total']
    fqa_df = pd.DataFrame()

    q_meta = {}
    for base_chart_name in base_charts:
        chart_names.append(base_chart_name)
        base_chart = seekerview.dashboard[base_chart_name]
        question = base_chart['X_facet']['field']
        if 'calc' in base_chart['X_facet']:
            calc = base_chart['X_facet']['calc']
        else:
            calc = 'count'
        q_meta[question] = {'calc': calc, 'chart_name': base_chart_name}
        answers = tile_df[tile_df['chart_name'] == base_chart_name]['x_field']
        answers = np.unique(answers).tolist()
        for answer in answers:
            qa_q_columns.append(question)
            qa_a_columns.append(answer)
            answer_values = tile_df[(tile_df['chart_name'] == base_chart_name) & (tile_df['x_field'] == answer)]['y_field']
            answer_values = np.unique(answer_values).tolist()
            for answer_value in answer_values:
                qav_q_columns.append(question)
                qav_a_columns.append(answer)
                qav_av_columns.append(answer_value)

    if len(qav_q_columns) > 0:
        qav_columns = pd.MultiIndex.from_arrays([qav_q_columns, qav_a_columns, qav_av_columns], names=['questions', 'answers', 'values'])
        qa_columns = pd.MultiIndex.from_arrays([qa_q_columns, qa_a_columns], names=['questions', 'answers'])
        fqav_df = pd.DataFrame(0.0, columns=qav_columns, index=f_index)
        msk = [(chart_name in chart_names) for chart_name in tile_df['chart_name']]
        for facet, facet_df in tile_df.groupby(tile_df[msk]['facet_tile']):
            for idx, facet_s in facet_df.iterrows():
                f = facet_s['facet_tile']
                q = facet_s['q_field']
                a = facet_s['x_field']
                av = facet_s['y_field']
                count = facet_s['metric']
                fqav_df.loc [f, (q, a, av)] = count
        # aggregate to qa (fact) level
        fqa_df = pd.DataFrame(0.0, columns=qa_columns, index=f_index)
        for facet in f_index:
            #for qa in fqa_df.columns:
            #use stable version of columns becaues of drop and insert into fqa_df
            for qa in qa_columns:
                q = qa[0]
                a = qa[1]
                question_field = q
                fact = chart['facts'][question_field]

                total = 0
                if q_meta[q]['calc'] == 'count':
                    if fact['value_type'] == 'boolean':
                        values, nr_respondents = get_fqa_v_respondents(fqav_df, q, a, facet)
                        for value in values:
                            value_code = answer_value_decode(value)
                            if value_code in ["Yes", "Total"]:
                                value_code = 1
                            elif value_code == "No":
                                value_code = 0
                            count = fqav_df[(q, a, value)][facet]
                            total = total + (value_code * count)
                        if nr_respondents > 0:
                            percentile = total / nr_respondents
                        else:
                            percentile = total
                        if fact['calc'] == 'w-avg':
                            fqa_df.loc [facet, (q, a)] = percentile
                        elif fact['calc'] == 'percentile':
                            fqa_df.loc [facet, (q, a)] = percentile
                        elif fact['calc'] == 'w-total':
                            fqa_df.loc [facet, (q, a)] = total
                        elif fact['calc'] == 'count':
                            fqa_df.loc [facet, (q, a)] = count
                    elif fact['value_type'] == 'ordinal':
                        answers, values, nr_respondents = get_fq_av_respondents(fqav_df, q, facet)
                        for aix in range(0, len(answers)):
                            answer = answers[aix]
                            value_code = answer_value_decode(answer)
                            if type(value_code) == str:
                                try:
                                    value_code = int(float(value_code))
                                except:
                                    value_code = 0
                            # normally one value returned from ES -> Total
                            value = values[aix]
                            total = total + (value_code * fqav_df[q, answer, value][facet])
                            if answer == a:
                                count = fqav_df[q, a, value][facet]
                        if nr_respondents > 0:
                            percentile = count / nr_respondents
                            mean = total / nr_respondents
                        else:
                            percentile = count
                            mean = total
                        if fact['calc'] == 'w-avg':
                            fqa_df.loc [facet, (q, 'w-avg')] = mean
                            if (q, a) in fqa_df.columns:
                                fqa_df.drop((q, a), axis=1, inplace=True)
                        elif fact['calc'] == 'percentile':
                            fqa_df.loc [facet, (q, a)] = percentile
                        elif fact['calc'] == 'w-total':
                            fqa_df.loc [facet, (q, a)] = total
                        elif fact['calc'] == 'count':
                            fqa_df.loc [facet, (q, a)] = count
                elif q_meta[q]['calc'] == 'percentile':
                    if fact['value_type'] == 'boolean':
                        percentile = 0
                        values, percentiles = get_fqa_v_respondents(fqav_df, q, a, facet)
                        for value in values:
                            if value in ["Yes", "Total"]:
                                percentile = fqav_df[(q, a, value)][facet]
                        if fact['calc'] == 'w-avg':
                            fqa_df.loc [facet, (q, a)] = percentile
                        elif fact['calc'] == 'percentile':
                            fqa_df.loc [facet, (q, a)] = percentile
                    elif fact['value_type'] == 'ordinal':
                        chart_name = q_meta[q]['chart_name']
                        mean = tiles_d[chart_name][facet]['meta_data']['mean']
                        if fact['calc'] == 'w-avg':
                            fqa_df.loc [facet, (q, 'w-avg')] = mean
                            if (q, a) in fqa_df.columns:
                                fqa_df.drop((q, a), axis=1, inplace=True)

    if len(fqa_df.index) > 0:
        stats_df = fqa_df.describe().transpose()
        stats_df['question'] = [t[0] for t in stats_df.index]
        stats_df['answer'] = [t[1] for t in stats_df.index]
        #corr_df = fqa_df.corr()
        #corr_df['question'] = [t[0] for t in corr_df.index]
        #corr_df['answer'] = [t[1] for t in corr_df.index]
        # compute the correlation between X and Y, X being the firt fact and Y the others
        # correlation is returned as a dataframe with X as the row (index) and Y as the columns
        qx = chart['X_facet']['field']
        for (q1, ax) in fqa_df.columns:
            if q1 != qx:
                continue
            for (qy, ay) in fqa_df.columns:
                # exclude 'All'
                stats_df.loc[(qy, ay), qx] = np.corrcoef(fqa_df[(qx, ax)][1:], fqa_df[(qy, ay)][1:])[0,1]
    stats_df.fillna(0, inplace=True)
    return stats_df

# aggs : { <
#GET survey/_search
#{
#  "size": 0,
#  "aggs": {
#    "regions": {
#      "terms": {
#        "field": "regions.keyword"
#      },
#      "aggs": {
#        "city": {
#          "terms": {
#            "field": "city.keyword"
#          },
#          "aggs": {
#            "children": {
#              "nested": {
#                "path": "children"
#              },
#              "aggs": {
#                "question": {
#                  "terms": {
#                    "field": "children.question.keyword",
#                    "size": 20,
#                    "min_doc_count": 1
#                  },
#                  "aggs": {
#                    "answer": {
#                      "terms": {
#                        "field": "children.answer.keyword",
#                        "size": 20,
#                        "min_doc_count": 1
#                      }
#                    }
#                  }
#                }
#              }
#            }
#          }
#        }
#      }
#    }
#  }
#}

def facet_aggregate(facet, charts):
    # Aggregate a facet when it occurs in a chart (storyboard) or it is visible on the sreen
    if facet.visible_pos > 0:
        return True;
    for chart_name, chart in charts.items():
        if chart['data_type'] == 'facet':
            if chart['X_facet']['field'] == facet.field:
                return True;
            if 'Y_facet' in chart:
                if chart['Y_facet']['field'] == facet.field:
                    return True;
    return False




#class Chart(object):
#    name = ""
#    chart_type = ""
#    db_chart = None
#    decoder = None
#    get_facet_by_field_name = None
#
#    def __init__(self, name, dashboard, get_facet_by_field_name, decoder=None, **kwargs):
#        self.name = name
#        self.chart_type = dashboard[name]['chart_type']
#        self.db_chart = dashboard[name]
#        self.get_facet_by_field_name = get_facet_by_field_name
#        self.decoder = decoder
#        self.db_chart['data'] = []
#        if 'key' not in self.db_chart['X_facet']:
#            self.db_chart['X_facet']['key'] = "key"
#        if 'metric' not in self.db_chart['X_facet']:
#            self.db_chart['X_facet']['metric'] = "doc_count"
#        if 'Y_facet' in self.db_chart:
#            if 'key' not in self.db_chart['Y_facet']:
#                self.db_chart['Y_facet']['key'] = "key"
#            if 'metric' not in self.db_chart['Y_facet']:
#                self.db_chart['Y_facet']['metric'] = "doc_count"

#    def json(self):
#        return json.dumps({'chart_type': self.chart_type, 'data': self.db_chart['data']})



def is_common(ngram):
    commonwords = [
        'the', 'be', 'and', 'of', 'a', 'in', 'to', 'have', 'it',
        'i', 'that', 'for', 'you', 'he', 'with', 'on', 'do', 'say', 'this',
        'they', 'us', 'an', 'at', 'but', 'we', 'his', 'from', 'that', 'not',
        'by', 'she', 'or', 'as', 'what', 'go', 'their', 'can', 'who', 'get',
        'if', 'would', 'her', 'all', 'my', 'make', 'about', 'know', 'will',
        'as', 'up', 'one', 'time', 'has', 'been', 'there', 'year', 'so',
        'think', 'when', 'which', 'then', 'some', 'me', 'people', 'take',
        'out', 'into', 'just', 'see', 'him', 'your', 'come', 'could', 'now',
        'than', 'like', 'other', 'how', 'then', 'its', 'our', 'two', 'more',
        'these', 'want', 'way', 'look', 'first', 'also', 'new', 'because',
        'day', 'more', 'use', 'no', 'man', 'find', 'here', 'thing', 'give', 
        'many', 'well'
        ]
    for word in ngram:
        if word in commonwords:
            return True
    return False

def clean_input(input):
    input = re.sub('\n+', " ", input)       #replace nl with a space
    input = re.sub('\[[0-9]*\]', "", input) #discard citation marks
    input = re.sub(' +', " ", input)        #replace multiple spaces with a sigle space
    input = bytes(input, "UTF-8")           #remove unicode characters
    input = input.decode("ascii", "ignore")
    input = input.split(' ')
    words = []
    for item in input:
        item = item.strip(string.punctuation)
        if len(item) > 1 or (item.lower() == 'a' or item.lower() == 'i'):
            words.append(item)
    return words


def get_ngrams(input, n):
    input = clean_input(input)
    output = {}
    for i in range(len(input)-n+1):
        newngram = input[i:i+n]
        if not is_common(newngram):
            newngram = " ".join(newngram)
            if newngram in output:
                output[newngram] = output[newngram] + 1
            else:
                output[newngram] = 1
    ngrams = OrderedDict(sorted(output.items(), key=lambda t: t[1], reverse=True))
    return ngrams

