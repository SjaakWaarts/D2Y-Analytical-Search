import pandas as pd
import numpy as np
from django.core.files import File
import glob, os
import time
from datetime import datetime
import urllib
import requests
import json

import app.models as models
from FMI.settings import BASE_DIR, ES_HOSTS

em_df = None

dashboard = {
    "uptake_col" : {
        'chart_type': "ColumnChart",
        'chart_title' : "Excito-Meter",
        'data_type'  : "aggr",
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "periods",
            'label'   : "Periods",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "uptake",
            'label'   : "Uptake"
            },
        },
    "uptake_line" : {
        'chart_type': "LineChart",
        'chart_title' : "Excito-Meter",
        'data_type'   : "aggr",
        #'controls'    : ['CategoryFilter'],
        'controls'    : ['NumberRangeFilter'],
        'listener'    : {'select' : {'colsort': None}},
        'X_facet'     : {
            'field'   : "periods",
            'label'   : "Yeas since inception",
            'total'   : False
            },
        'Y_facet'     : {
            'field'   : "uptake",
            'label'   : "Uptake",
            },
        'options'   : {
            "series"  : {0: {"type": 'line', 'lineWidth': 6 },},
            'curveType' : 'function',
            'legend'    : { 'position': 'right' },
            'height'  : 600,
            'hAxis'     : {'title': 'Years since inception'},
            #'vAxis' : {'viewWindow' : {'min': 0.0, 'max': 1.0}}
            'vAxis' : {'viewWindow' : {'min': 0.0}, 'title': 'Percent Uptake'}
            },
        }
    }

storyboard = [
    {'name'     : 'Uptake',
        'layout'   : {'rows' : [['uptake_line']]},
        'active'   : False,
    },
    ]

def correlate(uptake_field, IPC_field, correlations_field, FITTE_norm_field, CIU_field, regions_field, type_field, regulator_field):
    global em_df

    # use is to compare with None
    if em_df is None:
        return None

    for ix, row in em_df.iterrows():
        cor_bucket = 0
        if row['bucket'] == type_field:
            cor_bucket = 3
        cor_ciu = 0
        if abs(row['CIU'] - CIU_field) < 0.01:
            cor_ciu = 3
        elif abs(row['CIU'] - CIU_field) < 0.05:
            cor_ciu = 2
        elif abs(row['CIU'] - CIU_field) < 0.1:
            cor_ciu = 1
        cor_fitte = 0
        if abs(row['FITTE_norm'] - FITTE_norm_field) < 0.25:
            cor_fitte = 2
        elif abs(row['FITTE_norm'] - FITTE_norm_field) < 0.5:
            cor_fitte = 1
        cor_regions = (4 - abs(row['regions'] - regions_field)) / 4
        cor_natural = 0
        if row['regulator'] == regulator_field:
            cor_natural = 1
        em_df.loc[ix,'cor_bucket'] = cor_bucket
        em_df.loc[ix,'cor_ciu'] = cor_ciu
        em_df.loc[ix,'cor_fitte'] = cor_fitte
        em_df.loc[ix,'cor_regions'] = cor_regions
        em_df.loc[ix,'cor_natural'] = cor_natural
        em_df.loc[ix,'cor_total'] = cor_bucket + cor_ciu + cor_fitte + cor_regions + cor_natural
        if uptake_field != '':
            if row['uptake'] != uptake_field:
                em_df.loc[ix,'cor_total'] = 0

    em_df.sort_values(by=['cor_total'], ascending=False, inplace=True)
    em_df.reset_index(drop=True, inplace=True)
    correlation_li = []
    for ix in range(0, correlations_field):
        correlation_li.append((em_df.loc[ix,'IPC'], em_df.loc[ix,'name'], em_df.loc[ix,'year'], em_df.loc[ix,'cor_total'], 
                               em_df.loc[ix,'cor_bucket'], em_df.loc[ix,'cor_ciu'], em_df.loc[ix,'cor_fitte'],
                               em_df.loc[ix,'cor_regions'], em_df.loc[ix,'cor_natural']))
    return correlation_li

def uptake(correlations_field):
    global em_df

    # use is to compare with None
    if em_df is None:
        return None

    chart_data = []
    dt = pd.DataFrame()
    #dt['Uptake'] = ['00','01','02','03','04','05','06','07','08','09','10',
    #                '11','12','13','14','15','16','17','18','19','20']
    dt['Uptake'] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    avg = pd.Series(0.0 for _ in range(len(dt.index)))
    dt['Years since inception'] = avg
    categories = []
    for cor_ix in range(0, correlations_field):
        ipc = em_df.loc[cor_ix,'IPC']
        name = em_df.loc[cor_ix,'name']
        year = em_df.loc[cor_ix,'year']
        yearxx = em_df.loc[cor_ix,'yearxx']
        for yix in range(0, len(yearxx)):
            avg[yix] = avg[yix] + yearxx[yix]
        dt[ipc] = yearxx

    for yix in range(0, len(dt.index)):
        if correlations_field > 0:
            avg[yix] = avg[yix] / correlations_field
    dt['Average'] = avg

    chart_data.append(dt.columns.tolist())
    for ix, row in dt.iterrows():
        chart_data.append(row.tolist())

    tiles_d = {"uptake_col": {}, "uptake_line": {}}
    tiles_d["uptake_col"]['All'] = {'chart_data' : chart_data}  
    tiles_d["uptake_line"]['All'] = {'chart_data' : chart_data}   
    return tiles_d

def retrieve_ingredients():
    global em_df

    #excel_file = os.path.join(BASE_DIR, 'data/ingredients.xlsx')
    #try:
    #    em_df = pd.read_excel(excel_file, header=0)
    #except:
    #    cwd = os.getcwd()
    #    print("retrieve_ingredients: working dirtory is: ", cwd)
    #    print("retrieve_ingredients: excel_file: ", excel_file)
    #    return False

    #em_df.fillna("", inplace=True)
    #em_df['IPC'] = em_df.IPC.astype(str)
    #em_df = em_df[em_df.IPC != '']
    #em_df['IPC'] = pd.Series([str('00000000'+ipc)[-8:] for ipc in em_df['IPC']], index = em_df.index)
    #em_df.regions[em_df.regions == ''] = 0
    #em_df['regions'] = pd.Series([int(float(regions)) for regions in em_df['regions']], index = em_df.index)

    #em_df['cor_bucket'] = 0
    #em_df['cor_ciu'] = 0
    #em_df['cor_fitte'] = 0
    #em_df['cor_regions'] = 0
    #em_df['cor_natural'] = 0
    #em_df['cor_total'] = 0

    es_host = ES_HOSTS[0]
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    doc_type = "ingr_molecules"
    index = "excel_" + doc_type
    url = "http://" + host + ":9200/" + index
    query = json.dumps({
        "from"  : 0,
        "size" : 1000,
        "query": {
            "match_all": {}
            }
        })
    r = requests.get(url + "/" + doc_type + "/_search", headers=headers, data=query)
    results = json.loads(r.text)
    em_df = pd.DataFrame(columns=('IPC', 'name', 'uptake', 'year', 'nr_of_IPCs', 'nr_of_IPCs_SC', 'selling_IPCs', 'FITTE_score',
                                  'FITTE_norm', 'regions', 'flavor_classes', 'sales_val', 'sales_vol', 'tech_vol',
                                  'bucket', 'cost', 'use_level', 'low_medium_high', 'CIU', 'regulator', 'yearxx'))
    rownr = 0
    for hit in results['hits']['hits']:
        #s = pd.Series(index=em_df.columns)
        row = []
        for field in em_df.columns:
            #s[field] = hit['_source'][field]
            row.append(hit['_source'][field])
        #em_df.loc[hit['_source']['IPC']] = row, IPC is no longer unique with the different uptake sets
        em_df.loc[hit['_source']['id']] = row
        rownr = rownr + 1
    return True


def retrieve_uptake():
    global eu_df
    #eu_df = pd.DataFrame(columns=('Sum of 0', 'Sum of 1', 'Sum of 2', 'Sum of 3', 'Sum of 4', 'Sum of 5', 'Sum of 6',
    #                              'Sum of 7', 'Sum of 8', 'Sum of 9', 'Sum of 10', 'Sum of 11', 'Sum of 12', 'Sum of 13',
    #                              'Sum of 14', 'Sum of 15', 'Sum of 16', 'Sum of 17', 'Sum of 18', 'Sum of 19', 'Sum of 20'))
    eu_df = pd.DataFrame(columns=('IPC', 'period', 'perc'))
    csv_file = os.path.join(BASE_DIR, 'data/excitometer_uptake.csv')
    rownr = 0
    try:
        file = open(csv_file, 'r')
        pyfile = File(file)
    except:
        cwd = os.getcwd()
        print("retrieve_uptake: working dirtory is: ", cwd)
        print("retrieve_uptake: csv_file: ", csv_file)
        return False
    #for line in pyfile:
    #try:
    #    with open(csv_file, 'r') as pyfile:
    for line in pyfile:
        if rownr > 0: # skip header
            line = line.rstrip('\n')
            words = line.split(';')
            ipc = str('00000000'+words[0])[-8:]
            period = words[1]
            perc = float(words[2])
            eu_df.loc[rownr] = (ipc, period, perc)
        rownr = rownr + 1

    return True

