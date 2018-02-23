
from datetime import datetime
from django.core.files import File
import glob, os
import pickle
import requests
import urllib
from urllib.parse import urlparse
import re
from requests_ntlm import HttpNtlmAuth
from pandas import DataFrame
from bs4 import BeautifulSoup

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import seeker
import app.models as models
import app.crawl as crawl
import app.survey as survey
from FMI.settings import BASE_DIR


def put_settings(obj):
    indices_client = IndicesClient(models.client)
    index_name = obj._meta.es_index_name
    indices_client.close(index=index_name)
    kwargs = { "analysis": {
        "analyzer": {
            "default": {"tokenizer": "standard", "filter": ["synonym"]},
            "keepwords": {"tokenizer": "standard", "filter": ["keepwords"]},
            },
        "filter": {
            "synonym": {"type": "synonym", "synonyms_path": "synonym.txt"},
            "keepwords": {"type": "keep", "keep_words_path": "keepwords.txt"},
            }
        }
    }
    indices_client.put_settings(index=index_name, body=kwargs)
    indices_client.open(index=index_name)


def create_index_conf():
    indices_client = IndicesClient(models.client)
    index_name = 'conf'
    doc_type = index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)

# For excel only the index is created. The doc_types (mappings) are created
# when an excel file is uploaded. The mapping matches the columns of the worksheet
def create_index_excel(excel_filename):
    indices_client = IndicesClient(models.client)
    index_name = 'excel'
    if len(excel_filename):
        doc_type = os.path.splitext(excel_filename)[0]
        index_name = 'excel_' + doc_type
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    #indices_client.create(index=index_name)


def create_index_pi():
#   indices_client = IndicesClient(client=settings.ES_HOSTS)
    indices_client = IndicesClient(models.client)
    index_name = models.Review._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        doc_type=models.Review._meta.es_type_name,
        body=models.Review._meta.es_mapping,
        index=index_name
    )

def create_index_mi():
    indices_client = IndicesClient(models.client)
    index_name = models.PostMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        doc_type=models.PostMap._meta.es_type_name,
        body=models.PostMap._meta.es_mapping,
        index=index_name
    )


def create_index_si_sites():
    indices_client = IndicesClient(models.client)
    index_name = models.PageMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        doc_type=models.PageMap._meta.es_type_name,
        body=models.PageMap._meta.es_mapping,
        index=index_name
    )


def create_index_mi_feedly():
    indices_client = IndicesClient(models.client)
    index_name = models.FeedlyMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    #put_settings(models.FeedlyMap)
    indices_client.put_mapping(
        doc_type=models.FeedlyMap._meta.es_type_name,
        body=models.FeedlyMap._meta.es_mapping,
        index=index_name
    )

def create_index_scentemotion():
    indices_client = IndicesClient(models.client)
    index_name = models.ScentemotionMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    #put_settings(models.ScentemotionMap)
    indices_client.put_mapping(
        doc_type=models.ScentemotionMap._meta.es_type_name,
        body=models.ScentemotionMap._meta.es_mapping,
        index=index_name
    )

def create_index_studies():
    indices_client = IndicesClient(models.client)
    index_name = models.StudiesMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        doc_type=models.StudiesMap._meta.es_type_name,
        body=models.StudiesMap._meta.es_mapping,
        index=index_name
    )

def create_index_survey():
    indices_client = IndicesClient(models.client)
    index_name = models.SurveyMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    #put_settings(models.ScentemotionMap)
    # add qstfld fields
    es_mapping = models.SurveyMap._meta.es_mapping
    for qst, mapping in survey.qst2fld.items():
        fields = mapping[0]
        field_type = mapping[1]
        if field_type == 'nested_qst_ans':
            for field in fields:
                if field not in es_mapping['properties']:
                    es_mapping['properties'][field] = {}
                    es_mapping['properties'][field]['type'] = 'nested'
                    es_mapping['properties'][field]['properties'] = {}
                    es_mapping['properties'][field]['properties']['question'] = {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
                    es_mapping['properties'][field]['properties']['answer'] = {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
                        #'type'       : 'nested',
                        #'properties' : {
                        #    'question' : {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        #    'answer'   : {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        #    }
                        #},
    indices_client.put_mapping(
        doc_type=models.SurveyMap._meta.es_type_name,
        #body=models.SurveyMap._meta.es_mapping,
        body=es_mapping,
        index=index_name
        )


def create_index_elastic(index_choices, excel_filename):
    for index_choice in index_choices:
        if index_choice == 'conf':
            create_index_conf()
        elif index_choice == 'excel':
            create_index_excel(excel_filename)
        elif index_choice == 'pi':
            create_index_pi()
        elif index_choice == 'mi':
            create_index_mi()
        elif index_choice == 'si_sites':
            create_index_si_sites()
        elif index_choice == 'feedly':
            create_index_mi_feedly()
        elif index_choice == 'scentemotion':
            create_index_scentemotion()
        elif index_choice == 'studies':
            create_index_studies()
        elif index_choice == 'survey':
            create_index_survey()
            


def create_analyzer(index_choices):
    for index_choice in index_choices:
        if index_choice == 'pi':
            put_settings(models.Review)
        elif index_choice == 'mi':
            put_settings(models.PostMap)
        elif index_choice == 'si_sites':
            put_settings(models.PageMap)
        elif index_choice == 'feedly':
            put_settings(models.FeedlyMap)

def export_opml(index_choices, opml_filename):
    status = True
    for index_choice in index_choices:
        if index_choice == 'feedly':
            status = crawl.export_opml_feedly(opml_filename)
    return status

def import_opml(index_choices, opml_filename):
    status = True
    for index_choice in index_choices:
        if index_choice == 'feedly':
            status = crawl.import_opml_feedly(opml_filename)
    return status



def read_keywords(index_choices, keyword_filename):
    status = True
    for index_choice in index_choices:
        if index_choice == 'feedly':
            models.search_keywords[index_choice] = []
            keywords_input = ''
            keyword_file = os.path.join(BASE_DIR, 'data/' + keyword_filename)
            try:
                file = open(keyword_file, 'r')
                pyfile = File(file)
                for line in pyfile:
                    keyword = line.rstrip('\n')
                    models.search_keywords[index_choice].append(keyword)
                    if keyword.count(' ') > 0:
                        keyword = '"' + keyword + '"'
                    if keywords_input == '':
                        keywords_input = keyword
                    else:
                        keywords_input = keywords_input + ',' + keyword
                pyfile.close()
            except:
                cwd = os.getcwd()
                print("read_keywords: working dirtory is: ", cwd)
                print("read_keywords: keyword_file: ", keyword_file)
                return False
            models.FeedlySeekerView.facets_keyword[0].read_keywords = keywords_input

    return True
