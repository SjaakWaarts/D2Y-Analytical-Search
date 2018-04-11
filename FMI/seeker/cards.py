
import collections
import json
import urllib
import re
import string
import numbers
from collections import OrderedDict
import pandas as pd
import numpy as np
import math
from scipy import stats
#from statsmodels.stats.multicomp import pairwise_tukeyhsd
#from statsmodels.stats.multicomp import MultiComparison
import seeker.seekerview
import seeker.models
import seeker

def uptake(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark):
    chart_data = []
    meta_data = {}

    dt = pd.DataFrame()
    #dt['Uptake'] = ['00','01','02','03','04','05','06','07','08','09','10',
    #                '11','12','13','14','15','16','17','18','19','20']
    dt['Years since inception'] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    avg = pd.Series(0.0 for _ in range(len(dt.index)))
    dt['Average'] = avg
    categories = []
    # colums IPCs
    # rows years
    rownr = 0
    for hit in hits:
        ipc = hit['IPC']
        name = hit['name']
        year = hit['year']
        yearxx = hit['yearxx']
        for yix in range(0, len(yearxx)):
            avg[yix] = avg[yix] + yearxx[yix]
        dt[ipc] = yearxx
        rownr = rownr + 1

    for yix in range(0, len(dt.index)):
        if rownr > 0:
            avg[yix] = avg[yix] / rownr
    dt['Average'] = avg

    chart_data.append(dt.columns.tolist())
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())

    return chart_data, meta_data

# The paired t-test compares two sample sets. In our case the benchmark facet value, with all the
# other facet values. The facet itself is configured in the X_facet of the card, the score to compare
# is in the Y_facet.
# T-test is a hypothesis test that is used to compare the means of two populations.
# ANOVA is a statistical technique that is used to compare the means of more than two populations
def ttest(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark):
    chart_data = []
    meta_data = {}
    if len(hits) == 0:
        return chart_data, meta_data

    X_facet = chart['X_facet']
    X_field = X_facet['field']
    xfacet = seekerview.get_facet_by_field_name(X_field)
    Y_facet = chart['Y_facet']
    Y_field = Y_facet['field']
    yfacet = seekerview.get_facet_by_field_name(Y_field)
    significance = chart['significance']
    test_type = chart['test_type']

    # load data; rows are the respondents, columns the X_facet values
    ttest_dt = pd.DataFrame()
    rownr = 0
    benchmark_found = False
    X_key = ''
    for hit in hits:
        resp_id = hit['_source']['resp_id']
        X_key = hit['_source'][X_field]
        if len(benchmark) > 0:
            if X_key == benchmark[0]:
                benchmark_found = True
        if Y_field in hit['_source']:
            Y_key = yfacet.get_answer_hit(hit['_source'][Y_field], Y_facet)
            if Y_key is not None:
                Y_value_code = seeker.answer_value_decode(Y_key)
                ttest_dt.loc[resp_id, X_key] = Y_value_code
    ttest_dt.fillna(0, inplace=True)
    if benchmark_found:
        benchmark = benchmark[0]
    else:
        benchmark = X_key

    # run the anova
    samples = []
    for X_key in ttest_dt.columns:
        sample = np.array(ttest_dt[X_key], dtype=float)
        samples.append(sample)
    args = tuple(samples)
    f, p_anova = stats.f_oneway(*args)
    if test_type == 'one-tailed':
        p_ttest = p_anova / 2.0
    if p_anova < significance:
        sign = True
    else:
        sign = False

    # run the t-test
    dt = pd.DataFrame(index=['N', 'mean', 'std', 'tstat', 'p-anova', 'p-ttest', 'significant'])
    a = np.array(ttest_dt[benchmark], dtype=float)
    N = len(a)
    dt['t-test'] = ['N', 'mean', 'std', 'tstat', 'p-anova', 'p-ttest', 'significant']
    #dt['t-test'] = [
    #    {'label':'N', 'type': 'number'},
    #    {'label':'mean', 'type': 'number'},
    #    {'label':'std', 'type': 'number'},
    #    {'label':'tstat', 'type': 'number'},
    #    {'label':'p-anova', 'type': 'number'},
    #    {'label':'p-ttest', 'type': 'number'},
    #    {'label':'significant', 'type': 'boolean'}]
    dt[benchmark] = [N, a.mean(), a.std(), 1.0, p_anova, 0.0, sign]
    for X_key in ttest_dt.columns:
        if X_key == benchmark:
            continue
        b = np.array(ttest_dt[X_key], dtype=float)
        tstat, p_ttest = stats.ttest_ind(a, b, equal_var=True, nan_policy='omit')
        if test_type == 'one-tailed':
            p_ttest = p_ttest / 2.0
        if p_ttest < significance:
            sign = True
        else:
            sign = False
        dt[X_key] = [N, b.mean(), b.std(), tstat, p_anova, p_ttest, sign]

    chart_data.append(dt.columns.tolist())
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())

    return chart_data, meta_data


def bind_card(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark):
    chart_data = []
    meta_data = {}
    data_type = chart['data_type']

    if data_type == 'card_uptake':
        chart_data, meta_data = uptake(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark)
    ## routine already called from seekerview.render
    #elif data_type == 'card_ttest':
    #    chart_data, meta_data = ttest(seekerview, chart_name, chart, hits, aggregations, facet_tile_value, benchmark)

    return chart_data, meta_data
