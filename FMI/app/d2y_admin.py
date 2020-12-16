
from datetime import datetime
from django.core.files import File
from django.contrib.auth.models import Group, Permission, ContentType
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
import app.wb_excel as wb_excel
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
        body=models.FeedlyMap._meta.es_mapping,
        index=index_name
    )

def create_index_mail():
    indices_client = IndicesClient(models.client)
    index_name = models.MailMap._meta.es_index_name
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        body=models.MailMap._meta.es_mapping,
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
        body=models.ScentemotionMap._meta.es_mapping,
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
                    es_mapping['properties'][field]['properties']['question'] = {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
                    es_mapping['properties'][field]['properties']['answer'] = {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
                        #'type'       : 'nested',
                        #'properties' : {
                        #    'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        #    'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        #    }
                        #},
    indices_client.put_mapping(
        #body=models.SurveyMap._meta.es_mapping,
        body=es_mapping,
        index=index_name
        )

def create_index_dhk():
    indices_client = IndicesClient(models.client)
    index_name = 'recipes'
    if indices_client.exists(index_name):
        indices_client.delete(index=index_name)
    indices_client.create(index=index_name)
    indices_client.put_mapping(
        # ES7.0 does not support types anymore doc_type=index_name,
        body= {'properties' : wb_excel.recipes},
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
        elif index_choice == 'mail':
            create_index_mail()
        elif index_choice == 'scentemotion':
            create_index_scentemotion()
        elif index_choice == 'survey':
            create_index_survey()
        elif index_choice == 'dhk':
            create_index_dhk()
            


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

def auth_groups(auth_group_choices):
    for auth_group_choice in auth_group_choices:
        if auth_group_choice == 'iff':
            group = Group.objects.create(name='iff')
        elif auth_group_choice == 'divault':
            group = Group.objects.create(name='divault')
        elif auth_group_choice == 'dhk':
            group = Group.objects.create(name='dhk')
        elif auth_group_choice == 'd2y':
            group = Group.objects.create(name='d2y')

def auth_permissions(auth_permission_choices):
    ct = ContentType.objects.get(app_label='auth', model='user')
    for auth_permission_choice in auth_permission_choices:
        if auth_permission_choice == 'mi':
            permission = Permission.objects.create(codename='mi', name='mi', content_type=ct)
        elif auth_permission_choice == 'pi':
            permission = Permission.objects.create(codename='pi', name='pi', content_type=ct)
        elif auth_permission_choice == 'ci':
            permission = Permission.objects.create(codename='ci', name='ci', content_type=ct)
        elif auth_permission_choice == 'se':
            permission = Permission.objects.create(codename='se', name='se', content_type=ct)
        elif auth_permission_choice == 'edepot':
            permission = Permission.objects.create(codename='edepot', name='edepot', content_type=ct)


def auth_hasperm(auth_group_choices, auth_permission_choices):
    for auth_group_choice in auth_group_choices:
        group = Group.objects.get(name=auth_group_choice)
        for auth_permission_choice in auth_permission_choices:
            permisson = Permission.objects.get(codename=auth_permission_choice)
            group.permissions.add(permisson)


