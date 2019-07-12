
from datetime import datetime
from datetime import time
from datetime import timedelta
import glob, os
import shutil
import zipfile
import sys
import pickle
import urllib
import requests
import json
from urllib.parse import urlparse
import re
from slugify import slugify
from io import BytesIO
import cmislib
from cmislib.model import CmisClient
from FMI.settings import BASE_DIR, ES_HOSTS

#
# https://chemistry.apache.org/python/docs/index.html
#

def map_cmis(url, headers, client, repo, cmis_objtype, cmis_choices):
    # delete and re-create excel index
    if 'delete' in cmis_choices:
        # first delete
        r = requests.delete(url, headers=headers)
        return True

    objtype = repo.getTypeDefinition(cmis_objtype)

    # create mapping in excel index
    mapping = {
        'paths' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
        }
    converters={}
    for prop_name, prop in objtype.properties.items():
        #field = prop.displayName
        field = prop.id
        field_type = prop.getPropertyType()
        sub_fields = field.split('.')
        last_sub_field = sub_fields[len(sub_fields)-1]
        properties = mapping
        if len(sub_fields) > 1:
            for sub_field in sub_fields[:-1]:
                if sub_field not in properties:
                    if sub_field in nested_fields:
                        properties[sub_field] = {'type' : 'nested', 'properties' : {}}
                    else:
                        properties[sub_field] = {'properties' : {}}
                properties = properties[sub_field]['properties']
            if last_sub_field not in properties and last_sub_field in nested_fields:
                properties[last_sub_field] = {'type' : 'nested', 'properties' : {}}
                properties = properties[last_sub_field]['properties']
            field = last_sub_field
        if field_type == 'string':
            properties[field] = {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
        elif field_type == 'datetime':
            properties[field] = {'type' : 'date'}
        elif field_type == 'integer':
            properties[field] = {'type' : 'integer'}
        elif field_type == 'float':
            properties[field] = {'type' : 'float'}
        elif field_type == 'text':
            properties[field] = {'type' : 'text'}
        elif field_type == 'list':
            pass
        elif field_type == 'nested':
            properties[field] =  {'type' : 'nested', 
                                    'properties' : 
                                    {'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                        'prc' : {'type' : 'float'}}}
            pass
    mapping = json.dumps({'properties' : mapping})

    # delete and re-create excel index
    if 'recreate' in cmis_choices:
        # first delete
        r = requests.delete(url, headers=headers)
        r = requests.put(url, headers=headers)
        # next create
        doc_type = "cmis"
        r = requests.put(url + "/_mapping/" + doc_type, headers=headers, data=mapping)

    query = json.dumps({
        "query": {
            "match_all": {}
            }
        })


def load_cmis(cmis_foldername, cmis_objtype, cmis_choices):
    es_host = ES_HOSTS[0]
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    doc_type = "cmis"
    url = "http://" + host + ":9200/" + "cmis"

    cmis_dirname = os.path.join(BASE_DIR, 'data', 'cmis')

    client = CmisClient('http://cmis.alfresco.com/cmisatom', 'admin', 'admin')
    repositories = client.getRepositories()
    repo = client.defaultRepository
    info = repo.info
    #for k,v in info.items():
    #    print("key {0}, value: {1}".format(k, v))
    caps = repo.capabilities
    if 'recreate' in cmis_choices:
        map_cmis(url, headers, client, repo, cmis_objtype, cmis_choices)
    objtype = repo.getTypeDefinition(cmis_objtype)
    root = repo.getRootFolder()
    count = 1
    objects = root.getDescendants(depth=3)
    len(objects.getResults())
    for object in objects:
        doc = {}
        #repo_obj = repo.getObject(object.id)
        #for key,val in repo_obj.properties.items():
        #    print(key, val)
        doc_props = object.properties
        #print(object.name)
        #for prop_name, prop_value in doc_props.items():
        #    print(prop_name ,prop_value)
        doc_objtype = doc_props['cmis:objectTypeId']
        doc_objtype_str = str(doc_objtype)
        if doc_objtype_str == cmis_objtype:
            paths = object.getPaths()
            doc['paths'] = paths
            parents = object.getObjectParents()
            for prop_name, prop in objtype.properties.items():
                #field = prop.displayName
                field = prop.id
                field_type = prop.getPropertyType()
                prop_value = doc_props[prop_name]
                sub_doc = doc # in case of nesting
                sub_fields = field.split('.')
                last_sub_field = sub_fields[len(sub_fields)-1]
                if len(sub_fields) > 1:
                    for sub_field in sub_fields[:-1]:
                        if sub_field not in sub_doc:
                            if sub_field in nested_fields:
                                sub_doc[sub_field] = [{}]
                            else:
                                sub_doc[sub_field] = {}
                        else:
                            if sub_field in nested_fields:
                                sub_doc[sub_field].append({})
                        sub_field_value = sub_doc[sub_field]
                        if type(sub_field_value) is dict:
                            sub_doc = sub_doc[sub_field]
                        if type(sub_field_value) is list:
                            sub_doc = sub_doc[sub_field][len(sub_doc[sub_field])-1]
                    if last_sub_field not in properties and last_sub_field in nested_fields:
                        pass
                    field = last_sub_field
                if field_type == 'list':
                    if field not in doc:
                        sub_doc[field] = []
                    if prop_value != "":
                        if len(format) > 0:
                            delimiter = format
                            prop_value = str(prop_value)
                            if delimiter == '\\n':
                                items = prop_value.splitlines()
                            else:
                                items = prop_value.split(delimiter)
                            for item in items:
                                item = prop_value(item, decoder)
                                sub_doc[field].append(item)
                        else:
                            sub_doc[field].append(cell)
                elif field_type == 'nested':
                    if field not in sub_doc:
                        sub_doc[field] = []
                    if prop_value != '':
                        if answer == '':
                            nested_value = prop_value.split(',')
                            sub_doc[field].append({'val': nested_value[0], 'prc': float(nested_value[1])})
                        else:
                            sub_doc[field].append({'val': answer, 'prc': float(cell)})
                elif field_type == 'datetime':
                    sub_doc[field] = prop_value.strftime('%Y-%m-%d')
                elif field_type == 'text' or field_type == 'string':
                    prop_value = str(prop_value)
                    if field not in doc:
                        sub_doc[field] = prop_value
                    else:
                        sub_doc[field] = sub_doc[field] + format + prop_value
                else:
                    sub_doc[field] = prop_value
            # write metadata to ES
            id = object.properties['cmis:objectId']
            id = slugify(str(id))
            data = json.dumps(doc)
            print("load_cmis: write cmis line with id", id)
            r = requests.put(url + "/" + doc_type + "/" + id, headers=headers, data=data)
            print("load_cmis: writen cmis line with id", id)
            # download document
            doc_basename = doc_props.get('cmis:name', None)
            doc_mime_type = doc_props.get('cmis:contentStreamMimeType', None)
            doc_length = doc_props.get('cmis:contentStreamLength', 0)
            cmis_fullname = os.path.join(cmis_dirname, doc_basename)
            cmis_file_handler = object.getContentStream()
            buffer = cmis_file_handler.read()
            try:
                with open(cmis_fullname, 'w') as output_file:
                    output_file.write(buffer)
            except IOError as e:
                pass
            cmis_file_handler.close()
            count = count + 1

