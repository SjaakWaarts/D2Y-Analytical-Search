
from datetime import datetime
from datetime import time
from datetime import timedelta
from django.core.files import File
import glob, os
import sys
import pickle
import urllib
import requests
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import re
from requests_ntlm import HttpNtlmAuth
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import seeker
import app.models as models
import app.elastic as elastic
import app.survey as survey
from FMI.settings import BASE_DIR, ES_HOSTS

driver = None

#
# Mail crawl configuration
# The configuration is identified by the Subject.
# 

mails_conf = {
    "FW: today's juice news" : {
        'strip_forward' : True,
        'header_links' : 0,
        'footer_links' : 10
        },
    "today's juice news" : {
        'header_links' : 0,
        'footer_links' : 10
        }
    }

def read_scrape_page(url):
    try:
        print("read_page: scraping url ", url)
        html = urllib.request.urlopen(url)
        bs = BeautifulSoup(html.read(), "lxml")
        [script.decompose() for script in bs("script")]
        body = bs.get_text()
    except:
        body = ""
        print("Scrape: could not open url ", url)
    return body

def get_href_link_bodies(links):
    link_bodies = []
    for link in links:
        body = read_scrape_page(link[1])
        link_bodies.append((link[0], link[1], body))
    return link_bodies

# get all the links that point outside this site
def get_href_links(subject, bs):
    #exclude_url = urlparse(url).scheme+"://"+urlparse(url).netloc
    links = []
    if subject in mails_conf:
        mail_conf = mails_conf[subject]
    else:
        mail_conf = {}
    header_links = mail_conf.get('header_links', 0)
    footer_links = mail_conf.get('footer_links', 0)
    # get all the links that do not start with http
    for link_tag in bs.findAll("a", href=re.compile("^http.+")):
        link_href = link_tag.attrs['href']
        link_text = link_tag.text.replace("\r\n", " ").replace("\n", " ")
        if link_text == "":
            continue
        if (link_text, link_href) in links:
            continue
        links.append((link_text, link_href))
    return links[header_links:len(links)-footer_links]


