
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import urllib
import requests
import simplejson as json


### Global Defines
_AZURE_SEARCH_TEXT_ANALYZE_VERSION = '0.1.0'
_AZURE_SEARCH_API_VERSION = '2016-09-01'


# Azure Search Service Name ( never put space before and after = )
SEARCH_SERVICE_NAME="https://iffsedcommon01.search.windows.net"
# Azure Search API Admin Key ( never put space before and after = )
SEARCH_API_KEY="2CD55E6EA85EF943AC0762A6883A1AA8"

headers = {
    'Content-Type': "application/json; charset=utf-8",
    'api-key': SEARCH_API_KEY,
    'Accept': "application/json",
    }

ds_mi_pi = {
    }

def check_index(index_name):
    exists = False
    url = SEARCH_SERVICE_NAME + "/indexes/{0}?api-version={1}".format(index_name, _AZURE_SEARCH_API_VERSION)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        exists = True
    return exists

def delete_index(index_name):
    correct = False
    url = SEARCH_SERVICE_NAME + "/indexes/{0}?api-version={1}".format(index_name, _AZURE_SEARCH_API_VERSION)
    r = requests.delete(url, headers=headers)
    if r.status_code == 204:
        correct = True
    return correct


def create_index_pi():
    global SEARCH_SERVICE_NAME
    global SEARCH_API_KEY

    index_name = "ds-mi-fragr"
    if check_index(index_name):
        delete_index(index_name)

    url = SEARCH_SERVICE_NAME + "/indexes?api-version={0}".format(_AZURE_SEARCH_API_VERSION)
    #url = "https://iffsedcommon01.search.windows.net/indexes?api-version=2016-09-01"
    headers = {
        'Content-Type': "application/json; charset=utf-8",
        'api-key': SEARCH_API_KEY,
        'Accept': "application/json",
        }
    body = {
        'name' : index_name,
        'fields' : [
            {'name': 'id',          'type' : 'Edm.String', "key": True},
            {'name': 'perfume',     'type' : 'Edm.String'},
            {'name': 'review_date', 'type' : 'Edm.DateTimeOffset'},
            {'name': 'review',      'type' : 'Edm.String', "filterable": False, "sortable": False, "facetable": False},
            {'name': 'label',       'type' : 'Edm.String'},
            {'name': 'accords',     'type' : 'Collection(Edm.String)'}, 
            ]
        }
    r = requests.post(url, headers=headers, data=json.dumps(body))
    if r.status_code != 201:
        print("create_index_pi: failed to created index ", index_name)


def create_index_azure(index_choices):
    for index_choice in index_choices:
        if index_choice == 'pi':
            # create_index_pi0()
            create_index_pi()
        elif index_choice == 'mi':
            pass
        elif index_choice == 'si_sites':
            pass
        elif index_choice == 'feedly':
            pass