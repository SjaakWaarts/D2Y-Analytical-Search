﻿
from datetime import datetime
from datetime import time
from datetime import timedelta
from django.core.files import File
import glob, os
import shutil
import zipfile
import sys
import pickle
import urllib
import requests
import json
import pandas as pd
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from imapclient import IMAPClient
import html2text
import email
import re
import xml.etree.ElementTree as ET
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import app.models as models
import app.wb_excel as wb_excel
import app.elastic as elastic
import app.survey as survey
import app.mail as mail
import dhk_app.dhk_admin as dhk_admin
from FMI.settings import BASE_DIR, ES_HOSTS

driver = None

def abstract(map_s, row_s):
    global driver

    if driver == None:
        options = []
        options.append('--load-images=false')
        options.append('--ignore-ssl-errors=true')
        options.append('--ssl-protocol=any')
        #driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe', service_args=options)
        #driver = webdriver.PhantomJS(service_args=options)
        driver = webdriver.Chrome()
        driver.set_window_size(1120, 550)
        driver.set_page_load_timeout(3) # seconds
        driver.implicitly_wait(30) # seconds
    publication = row_s['Publication Number']
    url = row_s['url']
    try:
        #print("read_page: scraping url ", url)
        #html = urllib.request.urlopen(url)
        #bs = BeautifulSoup(html.read(), "lxml")
        #[script.decompose() for script in bs("script")]
        print("abstract: scraping publication", publication)
        driver.get(url)
        print("abstract: driver.get", publication)
    except:
        print("abstract: could not open url ", url)
    try:
        #time.sleep(3)
        abstract_tag = driver.find_element_by_id("PAT.ABE")
        print("abstract: driver.find_element_by_id", publication)
        print("abstract: abstract_tag.text", abstract_tag.text)
        tries = 0
        abstract_text = abstract_tag.text
        while len(abstract_text) == 0 and tries < 10000:
            abstract_text = abstract_tag.text
            tries = tries + 1
        print("abstract: abstract_text", abstract_text)
        print("abstract: TRIES", tries)
        #delay = 3 # seconds
        #abstract_tag = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, "PAT.ABE")))
    except:
        print("abstact: loading took too much time!")
        abstract_text = ""

    return abstract_text
        
def blindcode(map_s, row_s):
    blindcode_text = row_s['blindcode']
    if len(blindcode_text) and len(row_s['fragr_name']) > 0:
        blindcode_text = blindcode_text + '-' + row_s['fragr_name'][0:3]
    return blindcode_text
    

def decode_cell(cell_coded, decoder):
    cell_decoded = cell_coded
    try:
        cell_coded_numeric = int(float(cell_coded))
    except:
        cell_coded_numeric = -1
    for key, map in decoder.items():
        if cell_coded in map:
            cell_decoded = key
            break
        if cell_coded_numeric in map:
            cell_decoded = key
            break
    return cell_decoded


def load_excel(excel_filename, excelmap_filename, excel_choices, index_doc_name):
    global driver

    es_host = ES_HOSTS[0]
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    doc_type = os.path.splitext(excel_filename)[0]
    if index_doc_name == '':
        index = "excel_" + doc_type
    else:
        index = index_doc_name.split('/')[0]
        if len(index_doc_name.split('/')) > 1:
            doc_type = index_doc_name.split('/')[1]
        else:
            doc_type = index_doc_name

    url = "http://" + host + ":9200/" + index

    # delete and re-create excel index
    if 'delete' in excel_choices:
        # first delete
        r = requests.delete(url, headers=headers)
        return True

    converters={}
    converters['column'] = str
    if excelmap_filename == "":
        excelmap_filename = excel_filename
    excelmap_file = os.path.join(BASE_DIR, 'data', excelmap_filename)
    excel_file = os.path.join(BASE_DIR, 'data', excel_filename)
    try:
        mapping_df = pd.read_excel(excelmap_file, sheet_name="mapping", header=0, converters=converters)
    except:
        cwd = os.getcwd()
        print("load_excel: working dirtory is: ", cwd)
        print("load_excel: excelmap_file: ", excelmap_filename)
        return False

    mapping_df.fillna("", inplace=True)

    # create mapping in excel index
    mapping = {
        'subset' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
        }
    converters={}
    for map_key, map_s in mapping_df.iterrows():
        if 'header' in map_s:
            header = map_s.get('header', '').strip()
            header_defined = True
        else:
            header = ''
            header_defined = False
        column = map_s['column']
        question = map_s.get('question', '').strip()
        answer = map_s.get('answer', '').strip()
        nesting = map_s.get('nesting', '').replace(" ", "")
        nested_fields = nesting.split(',')
        field = map_s['field'].strip()
        sub_fields = field.split('.')
        last_sub_field = sub_fields[len(sub_fields)-1]
        if field == "":
            continue
        format = map_s['format']
        field_type = map_s['type']
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
            converters[column] = str
        elif field_type == 'date':
            properties[field] = {'type' : 'date'}
            converters[column] = str
        elif field_type == 'integer':
            properties[field] = {'type' : 'integer'}
            converters[column] = int
        elif field_type == 'float':
            properties[field] = {'type' : 'float'}
            converters[column] = float
        elif field_type == 'text':
            properties[field] = {'type' : 'text'}
            converters[column] = str
        elif field_type == 'list':
            pass
        elif field_type == 'nested':
            properties[field] =  {'type' : 'nested', 
                                    'properties' : 
                                    {'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                        'prc' : {'type' : 'float'}}}
            pass
            #properties[field] = {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
            #properties[field] = { 'properties' :
            #                     { field : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}}
            #                    }

    mapping = json.dumps({'properties' : mapping})

    # delete and re-create excel index
    if 'recreate' in excel_choices:
        # first delete
        r = requests.delete(url, headers=headers)
        r = requests.put(url, headers=headers)
        # next create
        r = requests.put(url + "/_mapping/" + doc_type, headers=headers, data=mapping)

    ## store document
    #data = json.dumps({
    #    "aop" : ["Creative"],
    #    "role" : "Creative Incubators",
    #    "name" : "113Industries, US   Razi Imam",
    #    "link" : "http://113industries.com/",
    #    "why"  : "A scientific research and innovation company made up of scientists and entrepreneurs, who works with leading Fortune 500 companies to help them invent their next generation products based on Social Design-Driven Innovation process and ensure their economic viability by rapidly innovating new products",
    #    "how"  : "Use the power of Big Data to analyze over 200,000 consumer conversations related to product consumption to generate an accurate profile of the consumers, their compensating behaviors and most of all their unarticulated needs.",
    #    "what" : "Social Design-Driven Innovation project to Discover insights, compensating behaviors and unarticulated needs of consumers in relation to air care in the home and auto space in the United States and United Kingdom Open new markets with innovative new products, solutions, and services or business model improvements that will create differentiation to IFF current and potential customers",
    #    "who" : "Razi Imam  razii@113industries.com",
    #    "country" : "USA",
    #    "contacts" : ["Razi Imam"],
    #    "company" : "113 Industries"
    #    })
    #r = requests.put(url + "/" + doc_type + "/1", headers=headers, data=data)
    # query excel
    query = json.dumps({
        "query": {
            "match_all": {}
            }
        })
    r = requests.get(url + "/" + doc_type + "/_search", headers=headers, data=query)
    results = json.loads(r.text)

    if header_defined:
        header_row = [0, 1]
    else:
        header_row = 0
    data_df = pd.read_excel(excel_file, sheet_name="data", header=header_row, index_col=None, converters=converters)
    # bug in pandas, first column is stored as index. Copy it back into the dataframe
    if header_defined:
        column_header = (mapping_df.iloc[0]['header'], mapping_df.iloc[0]['column'])
        if column_header not in data_df.columns:
            data_df[column_header] = data_df.index
    data_df.fillna("", inplace=True)
    bulk_data = []
    count = 1
    total_count = 0
    for key, row_s in data_df.iterrows():
        doc = None
        doc = {}
        #doc['subset'] = doc_type
        for map_key, map_s in mapping_df.iterrows():
            sub_doc = doc # in case of nesting
            field = map_s['field'].strip()
            if field == "":
                continue
            question = map_s.get('question', '').strip()
            answer = map_s.get('answer', '').strip()
            format = map_s['format']
            header = map_s.get('header', '').strip()
            decoder = map_s.get('decoder', '').strip()
            nesting = map_s.get('nesting', '').replace(" ", "")
            nested_fields = nesting.split(',')
            sub_fields = field.split('.')
            last_sub_field = sub_fields[len(sub_fields)-1]
            if decoder == "":
                decoder = {}
            else:
                decoder = json.loads(decoder)
            column = map_s['column']
            initial = getattr(map_s, 'initial', '')
            if header_defined:
                column_header = (header, column)
            else:
                column_header = column
            if column_header in row_s:
                cell = row_s[column_header]
            else:
                if len(initial) > 0:
                    cell = initial
                else:
                    cell = None
            field_type = map_s['type']
            if format == 'script':
                module = sys.modules[__name__]
                if hasattr(module, field):
                    doc[field] = getattr(module, field)(map_s, row_s)
            else:
                # incase no cell defined, doc[field] will not be populated
                if cell is not None:

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
                        if cell != "":
                            if len(format) > 0:
                                delimiter = format
                                cell = str(cell)
                                if delimiter == '\\n':
                                    items = cell.splitlines()
                                else:
                                    items = cell.split(delimiter)
                                for item in items:
                                    item = decode_cell(item, decoder)
                                    sub_doc[field].append(item)
                            else:
                                sub_doc[field].append(cell)
                    elif field_type == 'nested':
                        if field not in sub_doc:
                            sub_doc[field] = []
                        if cell != '':
                            if answer == '':
                                nested_value = cell.split(',')
                                sub_doc[field].append({'val': nested_value[0], 'prc': float(nested_value[1])})
                            else:
                                sub_doc[field].append({'val': answer, 'prc': float(cell)})
                    elif field_type == 'date':
                        cell = str(cell)
                        if len(format) > 0:
                            sub_doc[field] = datetime.strptime(cell, format).strftime('%Y-%m-%d')
                        else:
                            sub_doc[field] = cell
                        #doc[field] = datetime.strptime(cell, format).date()
                    elif field_type == 'text' or field_type == 'string':
                        cell = decode_cell(cell, decoder)
                        cell = str(cell)
                        if field not in doc:
                            sub_doc[field] = cell
                        else:
                            sub_doc[field] = sub_doc[field] + format + cell
                    else:
                        cell = decode_cell(cell, decoder)
                        sub_doc[field] = cell

        if 'id' in doc:
            id = doc['id']
        else:
            id = str(count)
        data = json.dumps(doc)
        print("load_excel: write excel line with id", id)
        r = requests.put(url + "/" + doc_type + "/" + id, headers=headers, data=data)
        print("load_excel: written excel line with id", id)
        count = count + 1

    #if driver != None:
    #    driver.quit()
    return True

def load_mail(email_choices, email_address, email_password):
    #server = IMAPClient('imap.kpnmail.nl', use_uid=True)
    server = IMAPClient('imap.deheerlijkekeuken.nl', use_uid=True, ssl=False)
    resp = server.login(email_address, email_password)
    resp = resp.decode()
    if resp != "LOGIN Ok.":
        return False
    select_info = server.select_folder('INBOX')
    print('%d messages in INBOX' % select_info[b'EXISTS'])
    messages = server.search(['ALL'])
    response = server.fetch(messages, ['ENVELOPE', 'RFC822', 'BODY[TEXT]'])
    server.logout()

    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.bypass_tables = False
    bulk_data = []
    count = 0
    total_count = 0
    for msgid, raw_email in response.items():
        envelope = raw_email[b'ENVELOPE']
        post_id = envelope.message_id.decode()
        subject = envelope.subject.decode()
        from_addr = envelope.from_[0].mailbox.decode() + '@' + envelope.from_[0].host.decode()
        to_addr = envelope.to[0].mailbox.decode() + '@' + envelope.to[0].host.decode()
        print('ID #%d: "%s" received %s' % (msgid, subject, envelope.date))
        raw_email_string = raw_email[b'RFC822'].decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        body_text = ""
        # this will loop through all the available multiparts in mail
        for part in email_message.walk():
            if part.get_content_type() == "text/plain": # ignore attachments
                body = part.get_payload(decode=True)
                body_text = body.decode('utf-8')
                links = set()
            if part.get_content_type() == "text/html": # ignore attachments
                body = part.get_payload(decode=True)
                body = body.decode('utf-8').strip()
                bs = BeautifulSoup(body, "lxml")
                body_tag = bs.find('body')
                body_text = body_tag.text
                links = mail.get_href_links(subject, bs)
                link_bodies = mail.get_href_link_bodies(links)
                #body = text_maker.handle(body)
                break
        from_index = body_text.find("From:")
        if from_index > 0:
            nl_index = body_text.find("\n", from_index)
            txt = body_text[from_index+6:nl_index].replace('\r','')
            from_addr = txt
        sent_index = body_text.find("Sent:")
        if sent_index > 0:
            nl_index = body_text.find("\n", sent_index)
            txt = body_text[sent_index+5:nl_index].strip().split(' ')
            txt = ' '.join(txt[1:4])
            #conversion fails because of month in local language
            #published_date = datetime.strptime(txt, "%d %B %Y").date()
        to_index = body_text.find("To:")
        if to_index > 0:
            nl_index = body_text.find("\n", to_index)
            txt = body_text[to_index+3:nl_index]
            to_addr = txt
        subject_index = body_text.find("Subject:")
        if subject_index > 0:
            nl_index = body_text.find("\n", subject_index)
            txt = body_text[subject_index+9:nl_index]
            subject = txt
        body_text.replace("\r\n", " ")
        body_text.replace("\n", " ")
        body_text.replace("  ", " ")
        mail_doc = models.MailMap()
        mail_doc.post_id = msgid
        mail_doc.to_addr = to_addr
        mail_doc.from_addr = from_addr
        mail_doc.published_date = envelope.date.date()
        #mail_doc.links = [link[0] for link in links]
        mail_doc.links = link_bodies
        mail_doc.subject = subject
        mail_doc.url = ""
        mail_doc.body = body_text
        data = elastic.convert_for_bulk(mail_doc, 'update')
        bulk_data.append(data)
        count = count + 1
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("load_mail: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1

    bulk(models.client, actions=bulk_data, stats_only=True)

    return True


def load_bestmatch(cft_filename):
    ml_file = 'data/' + cft_filename
    cft_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False)
    cft_df.fillna(0, inplace=True)
    cft_df.index = cft_df['cft_id']
    bulk_data = []
    count = 0
    total_count = 0
    for cft_id, cft_s in cft_df.iterrows():
        se = models.bestmatchMap()
        se.cft_id = cft_id
        se.dataset = "ingredients"
        se.ingr_name = cft_s.ingr_name
        se.IPC = cft_s.IPC
        se.supplier = cft_s.supplier
        se.olfactive = cft_s.olfactive
        se.region = cft_s.region
        se.review = cft_s.review
        se.dilution = cft_s.dilution
        se.intensity = cft_s.intensity

        percentile = {}
        for col in cft_s.index:
            col_l = col.split("_", 1)
            fct = col_l[0]
            if fct not in ["mood", "smell", "negative", "descriptor", "color", "texture"]:
                continue
            if fct not in percentile.keys():
                percentile[fct] = []
            val = col_l[1]
            prc = cft_s[col]
            if prc > 0:
                #percentile[fct].append((val, "{0:4.2f}".format(prc)))
                percentile[fct].append((val, prc))

        se.mood = percentile["mood"]
        se.smell = percentile["smell"]
        se.negative = percentile["negative"]
        se.descriptor = percentile["descriptor"]
        se.color = percentile["color"]
        se.texture = percentile["texture"]

        data = elastic.convert_for_bulk(se, 'update')
        bulk_data.append(data)
        count = count + 1
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("load_bestmatch: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1

    bulk(models.client, actions=bulk_data, stats_only=True)
    pass


def load_recipes(recipes_foldername):
    if os.path.isdir(recipes_foldername):
        for filename in os.listdir(recipes_foldername):
            fullname = os.path.join(recipes_foldername, filename)
            if os.path.isfile(fullname) and filename[0] != '~':
                if os.path.splitext(filename)[1] == '.docx':
                    dhk_admin.ingest_recipe(filename, fullname)
                    print("load_recipe: written recipe with id", filename)


def map_survey(survey_filename, map_filename):
    if map_filename != '':
        survey.qa = survey.qa_map(map_filename)
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    ml_file = 'data/' + survey_filename
    survey_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False)
    survey_df.fillna(0, inplace=True)
    field_map, col_map, header_map = survey.map_columns(survey_name, survey_df.columns)
    return field_map, col_map, header_map

def load_survey1(request, survey_filename, map_filename):
    if map_filename != '':
        survey.qa = survey.qa_map(map_filename)
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    ml_file = 'data/' + survey_filename
    converters={}
    survey_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False, dtype=object)
    # col_map[column]: (field, question, answer, dashboard)
    # field_map[field]: [question=0, answer=1, column=2, field_type=3)]
    field_map , col_map, header_map = survey.map_columns(survey_name, survey_df.columns)
    converters={}
    for col, map in col_map.items():
        if map[3] == 'text':
            converters[col] = str
    survey_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False, converters=converters)
    survey_df.fillna(0, inplace=True)
    survey_df.index = survey_df[field_map['resp_id'][0][2]]
    bulk_data = []
    count = 0
    total_count = 0
    for resp_id, survey_s in survey_df.iterrows():
        resp_id = survey.answer_value_to_string(survey_s[field_map['resp_id'][0][2]])
        blindcode = survey.answer_value_to_string(survey_s[field_map['blindcode'][0][2]])
        #sl = models.SurveyMap()
        #sl.resp_id = resp_id+"_"+blindcode
        #sl.survey  = survey_name
        data = {}
        #data['_id'] = resp_id+"_"+blindcode
        #data['resp_id'] = resp_id+"_"+blindcode
        #data['survey'] = survey_name
        for field, maps in field_map.items():
            # resp_id is the unique id of the record, this is already set above
            #if field == 'resp_id':
            #    continue
            # map: 0=question, 1=answer, 2=column, 3=field_type, 4=keys
            map = maps[0]
            answer_value = survey_s[map[2]]
            answer_value = survey.answer_value_to_string(answer_value)
            answer_value = survey.answer_value_encode(map[0], map[1], field, answer_value)
            answer_values = [answer_value]
            # column mapping, no question
            if map[0] == None:
                # in case of multiple mapping search for the column that has a value
                for ix in range(1, len(maps)):
                    map = maps[ix]
                    answer_value_2 = survey_s[map[2]]
                    answer_value_2 = survey.answer_value_to_string(answer_value_2)
                    answer_values.append(answer_value_2)
                    if (field == 'blindcode'):
                        if answer_value_2 != '':
                            answer_value = answer_value + '-' + answer_value_2[:3]
                    else:
                        if len(answer_value_2) > len(answer_value):
                            answer_value = answer_value_2
                if map[3] == 'dict':
                    answer_value = survey.answer_values_dict(answer_values, map[4])
                #setattr(sl, field, answer_value)
                elastic.convert_field(data, field, map, answer_value)
            # question mapping, no answer
            elif map[1][0] == '_':
                #setattr(sl, field, answer_value)
                elastic.convert_field(data, field, map, answer_value)
            # answer mapping
            else:
                #setattr(sl, field, {map[1]: answer_value})
                #attr = getattr(sl, field)
                for ix in range(0, len(maps)):
                    map = maps[ix]
                    answer_value = survey_s[map[2]]
                    answer_value = survey.answer_value_to_string(answer_value)
                    answer_value = survey.answer_value_encode(map[0], map[1], field, answer_value)
                    #attr[map[1]] = answer_value
                    ##attr.append({map[1]: answer_value})
                    elastic.convert_field(data, field, map, answer_value)
        #data = elastic.convert_for_bulk(sl, 'update')
        survey.map_header(request, survey_name, data)
        data['_id'] = survey.map_id(survey_name, data)
        data = elastic.convert_data_for_bulk(data, 'survey', '_doc', 'update')
        bulk_data.append(data)
        count = count + 1
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("crawl_survey: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1
            #break

    bulk(models.client, actions=bulk_data, stats_only=True)
    pass


def load_survey(request, survey_filename, map_filename):
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    if survey_name == 'fresh and clean':
         load_survey1(request, survey_filename, map_filename)
    elif survey_name == 'orange beverages':
         load_survey1(request, survey_filename, map_filename)
    elif survey_name == 'global panels':
         load_survey1(request, survey_filename, map_filename)
    elif survey_name == 'invictus ul':
         load_survey1(request, survey_filename, map_filename)
