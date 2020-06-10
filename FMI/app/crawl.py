
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

si_sites = {
    'gci'   : {
        'site_url'  : 'http://www.gcimagazine.com/',
        'sub_sites' : {
            'gci'   : 'http://www.gcimagazine.com/'},
        },
    }

driver = None

class Crawler:
    site_name = ''
    pages = set()
    bulk_data = []
    nrpages = 5

    def __init__(self, from_dt, site, nrpages):
        self.site = site
        self.nrpages = nrpages
        self.from_dt = from_dt
        # Add some recent user agent to prevent amazon from blocking the request 
        # Find some chrome user agent strings  here https://udger.com/resources/ua-list/browser-detail?browser=Chrome
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    # read the content of a page into BeautifulSoup
    def read_page(self, url):
        try:
            print("read_page: scraping url ", url)
            #html = urllib.request.urlopen(url)
            #bs = BeautifulSoup(html.read(), "lxml")
            page = requests.get(url, headers=self.headers)
            if page.status_code != 200:
                print("Could not read page: "+url)
                return false
            bs = BeautifulSoup(page.content, "lxml")
            [script.decompose() for script in bs("script")]
        except:
            print("Scrape: could not open url ", url)
        return bs

    # Step though all summery pages (Next, Pagination) and from each summary page get all the link refering to the articles
    def get_pagination_links(self, sub_site):
        include_url = urlparse(sub_site).scheme+"://"+urlparse(sub_site).netloc
        links = set()
        url = sub_site
        page_nr = 0
        page_size = 10
        link_count = 1
        links.add(sub_site)
        return links

    # get all the links that point within this site
    def get_internal_links(self, url, bs):
        include_url = urlparse(url).scheme+"://"+urlparse(url).netloc
        links = set()
        link_count = 0
        for link_tag in bs.findAll("a", href=re.compile("^(/|.*"+include_url+")")) and link_count < self.nrpages:
            if link_tag.attrs['href'] is not None:
                if link_tag.attrs['href'] not in links:
                    if link_tag.attrs['href'].startswith('/'):
                        link = include_url+link_tag.attrs['href']
                    else:
                        link = link_tag.attrs['href']
                    links.add(link)
                    link_count = link_count + 1
        return links

    # get all the links that point outside this site
    def get_external_links(self, url, bs):
        exclude_url = urlparse(url).scheme+"://"+urlparse(url).netloc
        links = set()
        # get all the links that do not start with http
        for link_tag in bs.findAll("a", href=re.compile("^http.+")) and link_count < self.nrpages:
            link = link_tag.attrs['href']
            if len(exclude_url) > 3: # ://
                if not link_tag.attrs['href'].startswith(eclude_url):
                    links.add(link)
            else:
                links.add(link)
        return links

    # for this page (url) scrape its context and map this to the elasticsearch record (pagemap)
    def scrape_page_map(self, sub_site, url, bs):
        id = url
        site_url = urlparse(url).netloc.split('.')[1]
        sub_site_url = urlparse(url).path.split('/')
        sub_site_name = '-'.join(sub_site[1:-1])
        if sub_site_name == '':
            sub_site_name = 'Home'
        pagemap             = models.PageMap()

        pagemap.page_id     = id
        pagemap.site        = self.site
        pagemap.sub_site    = sub_site
        pagemap.url         = url
        pagemap.section     = ''

        try: # get posted date
            pagemap.published_date = datetime.today()
        except:
            pass
        try: # get page
            pagemap.page        = bs.get_text()
        except:
            pass
        try: # get title
            if bs.title != None:
                pagemap.title   = bs.title.text
            else:
                pagemap.title   = ''
        except:
            pass

        data = elastic.convert_for_bulk(pagemap, 'update')
        return data

def crawl_si_site(from_dt, site_choice, nrpages):
    crawler = Crawler (from_dt, site_choice, nrpages)
    si_site = si_sites[site_choice]
    sub_sites = si_site.sub_sites
    site_url = si_site.site_url
           
    for sub_site, sub_site_url in sub_sites.items():
        bs = crawler.read_page(sub_site_url)
        links = crawler.get_internal_links(sub_site_url, bs)        
        for link in links:
             bs = crawler.read_page(link)
             apf.pages.add(link)
             data = apf.scrape_page_map(sub_site, link, bs)
             apf.bulk_data.append(data)
    
    bulk(models.client, actions=apf.bulk_data, stats_only=True)


#****************************** APF Crawler *****************************************

class AFPCrawler(Crawler):

    def get_pagination_links(self, sub_site):
        include_url = urlparse(sub_site).scheme+"://"+urlparse(sub_site).netloc
        links = set()
        url = sub_site
        page_nr = 0
        page_size = 10
        link_count = 0
        while url != None and link_count < self.nrpages:
            bs = self.read_page(url)
            blog_posts_tag = bs.find("div", class_="blog-posts")
            for link_tag in blog_posts_tag.findAll("a", href=re.compile("^(/|.*"+include_url+")")):
                if link_tag.attrs['href'] is not None:
                    if link_tag.attrs['href'] not in links:
                        if link_tag.attrs['href'].startswith('/'):
                            link = include_url+link_tag.attrs['href']
                        else:
                            link = link_tag.attrs['href']
                        links.add(link)
                        link_count = link_count + 1
            navigation_tag = bs.find("nav", class_="nav-below")
            if navigation_tag != None:
                next_tag = navigation_tag.find("span", class_="nav-next")
                if next_tag != None:
                    next_url = next_tag.parent.attrs['href']
                else:
                    next_url = None
            url = next_url
        return links


    def scrape_page_map(self, sub_site, url, bs):
        id = url
        pagemap             = models.PageMap()
        pagemap.page_id     = id
        pagemap.site        = self.site
        pagemap.sub_site    = sub_site
        pagemap.url         = url

        # get posted date
        # <span class="entry-date">May 23, 2017</span>
        try:
            pagemap.published_date = datetime.today()
            entry_date_tag = bs.find("span", class_="entry-date")
            published = entry_date_tag.text
            pagemap.published_date = datetime.strptime(published, '%B %d, %Y').date()
        except:
            pass

        # get page
        # <section class="entry-content">
        try:
            pagemap.page = bs.get_text()
            entry_content_tag = bs.find("section", class_="entry-content")
            pagemap.page = entry_content_tag.text
        except:
            pass
        # get title
        # <h1 class="entry-title"></h1>  text
        try:
            if bs.title != None:
                pagemap.title   = bs.title.text
            else:
                pagemap.title   = ''
            entry_title_tag = bs.find("h1", class_="entry-title")
            pagemap.title = entry_title_tag.text
        except:
            pass
        # get section
        try:
            pagemap.section = sub_site
        except:
            pass

        data = elastic.convert_for_bulk(pagemap, 'update')
        return data


def crawl_apf(from_dt, scrape_choices, nrpages):
    apf = AFPCrawler (from_dt, 'APF', nrpages)
    sub_sites = {}
    site_url = 'https://apf.org/'
    for scrape_choice in scrape_choices:
        if scrape_choice == 'blog':
            sub_sites['blog'] = site_url + '/blog'
        if scrape_choice == 'publications':
            sub_sites['blog'] = site_url + '/publications'
           
    for sub_site, sub_site_url in sub_sites.items():
        links = apf.get_pagination_links(sub_site_url)        
        for link in links:
             bs = apf.read_page(link)
             apf.pages.add(link)
             data = apf.scrape_page_map(sub_site, link, bs)
             apf.bulk_data.append(data)
    
    bulk(models.client, actions=apf.bulk_data, stats_only=True)


#****************************** Cosmetics Crawler *****************************************

class CosmeticsCrawler(Crawler):

    def __init__(self, from_dt,site, nrpages):
        global driver

        if driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            driver = webdriver.Chrome(chrome_options=options)
        super(CosmeticsCrawler, self).__init__(from_dt, site, nrpages)

    # read the content of a page using a driver into BeautifulSoup
    def read_page(self, url):
        global driver

        bs = None
        try:
            print("read_page: scraping url ", url)
            driver.get(url)
            bs = BeautifulSoup(driver.page_source, "lxml")
            [script.decompose() for script in bs("script")]
        except:
            print("Scrape: could not open url ", url)
        return bs

    def get_pagination_links(self, sub_site):
        global driver

        include_url = urlparse(sub_site).scheme+"://"+urlparse(sub_site).netloc
        links = set()
        url = sub_site
        bs = self.read_page(url)
        page_nr = 1
        page_found = True
        page_size = 10
        link_count = 0
        while page_found and link_count < self.nrpages:
            #box_1_tag = bs.find("div", class_="box_1")
            #for link_tag in box_1_tag.findAll("a", href=re.compile("^(/|.*"+include_url+")")):
            # for product catalog
            products_search_results_tag = bs.find('div', {'data-content':"products_search_results"})
            if products_search_results_tag:
                articles_tag = products_search_results_tag
            else:
                # for market trends
                layout_main_tag = bs.find('div', class_="Layout-main")
                articles_tag = layout_main_tag
            for article_tag in articles_tag.find_all('article'):
                link_tag = article_tag.div.h3.a
                if link_tag.attrs['href'] is not None:
                    if link_tag.attrs['href'] not in links:
                        if link_tag.attrs['href'].startswith('/'):
                            link = include_url+link_tag.attrs['href']
                        else:
                            link = link_tag.attrs['href']
                        links.add(link)
                        link_count = link_count + 1
            #result_count_tag = bs.find("span", class_="result_count")
            #if result_count_tag != None:
            #    result_count_list = result_count_tag.text.split()
            #    result_count = int(float(result_count_list[4]))
            #else:
            #    result_count = page_size
            #navigation_tag = bs.find(id="navigation")
            #if navigation_tag != None:
            #    next_tag = navigation_tag.find("span", class_="next")
            #    if next_tag != None:
            #        next_url = include_url + next_tag.find("a").attrs['href']
            #    else:
            #        next_url = None
            #else:
            #    page_nr = page_nr + 1
            #    if page_nr * page_size > result_count:
            #        next_url = None
            #    else:
            #        next_url = sub_site + '/(offset)/{}'.format(page_nr)
            page_nr = page_nr + 1
            url = sub_site + '?page=' + str(page_nr)
            products_search_results_tag = bs.find('div', {'data-content':"products_search_results"})
            pagination_list_tag = bs.find('ul', class_="Pagination-list")
            pagination_item_tag = pagination_list_tag.find('a', {'data-page-number':str(page_nr)})
            pagination_item_elm = driver.find_element_by_xpath('//a[@data-page-number="'+str(page_nr)+'"]')
            if pagination_item_elm:
                #pagination_item_elm.click()
                driver.execute_script("arguments[0].click();", pagination_item_elm)
                bs = BeautifulSoup(driver.page_source, "lxml")
            else:
                page_found = False
        return links


    def scrape_page_map(self, sub_site, url, bs):
        id = url
        pagemap             = models.PageMap()
        pagemap.page_id     = id
        pagemap.site        = self.site
        pagemap.sub_site    = sub_site
        pagemap.url         = url

        article_tag = bs.find('article')
        try: # posted date
            published = article_tag.find('time').text
            pagemap.published_date = datetime.strptime(published, '%d-%b-%Y').date()
        except:
            pass
        try: # title
            if bs.title != None:
                pagemap.title = bs.title.text
            else:
                pagemap.title = article_tag.header.h1.text
        except:
            pass
        try: # section
            if sub_site in ['Skin-care', 'Hair-care']:
                pagemap.section = article_tag.header.p.text.strip()
            else:
                pagemap.section = 'blog'
        except:
            pass
        try: # img_src
            pagemap.img_src = article_tag.header.figure.img.attrs['src']
        except:
            pass
        try: # page
            pagemap.page = article_tag.find('div', class_='Detail-content').text
        except:
            pass


        data = elastic.convert_for_bulk(pagemap, 'update')
        return data


def crawl_cosmetic(from_dt, scrape_choices, nrpages):
    cosmetic = CosmeticsCrawler(from_dt, 'Cosmetics', nrpages)
    sub_sites = {}
    if len(scrape_choices) == 0:
        sub_sites.add(site)
#   for site in ['http://www.cosmeticsdesign.com', 'http://www.cosmeticsdesign-europe.com', 'http://www.cosmeticsdesign-asia.com']:
    for site_url in ['https://www.cosmeticsdesign.com']:
        for scrape_choice in scrape_choices:
            if scrape_choice == 'product':
                sub_sites['Skin-care'] = site_url + '/Product-Categories/Skin-Care'
                sub_sites['Hair-care'] = site_url +'/Product-Categories/Hair-Care'
            if scrape_choice == 'market':
                sub_sites['Market-Trends'] = site_url + '/Market-Trends'
                sub_sites['Brand-Innovation']= site_url +'/Brand-Innovation'

    for sub_site, sub_site_url in sub_sites.items():
        links = cosmetic.get_pagination_links(sub_site_url)
        for link in links:
            bs = cosmetic.read_page(link)
            cosmetic.pages.add(link)
            data = cosmetic.scrape_page_map(sub_site, link, bs)
            cosmetic.bulk_data.append(data)

    bulk(models.client, actions=cosmetic.bulk_data, stats_only=True)

#
# FEEDLY
#

def crawl_feedly(from_dt, rss_field):
    global headers

    today = datetime.now()
    days = timedelta(days=31)
    yesterday = today - days
    s = yesterday.timestamp()
    t = time(0, 0)
    dt = datetime.combine(from_dt, t)
    s = dt.timestamp()
    #datetime.datetime.fromtimestamp(s).strftime('%c')
    ms = s * 1000
    newerthan = "{:.0f}".format(ms)
    headers = {
        #sjaak.waarts@gmail.com (expires on 2020-jul-10)
        "Authorization" : "Azsr6uaruKGMnymDVmYUkDrF33mC2csnyv1OScN4hpsnH5w2ngb0zEBlwyAo4izpB3W3a2RYDAW99xYFM61U5g0U13M59tiAjZFqHkVpAXVeG8PAYl5Y060wwErrxvjj12UNeQ4bk23mzCcoa9AAJtBvUMl_DZl2-jaX0cf_vmlZuVMQh-B2Srv1FUEkno3fbVJtTdZeOc1YP29aRluNyYndpm2CWYKFjaeL1LicHbObhdjgHQAZ-EFUUDCA:feedlydev"
        }

    params_streams = {
#       "count"     : "100",
        "count"     : "1000",
        "ranked"    : "newest",
        "unreadOnly": "false",
        "newerThan" : newerthan
        }
    #url = "http://cloud.feedly.com/v3/profile"
    #r = requests.get(url, headers=headers)
    url = "http://cloud.feedly.com/v3/subscriptions"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return False
    feeds = r.json()
    for feed in feeds:
        feed_id = feed['id']
        feed_title = feed['title'].encode("ascii", 'replace')
        # the category label can contain the subset and category name
        category_label = feed['categories'][0]['label']
        label_split = category_label.split('-')
        if len(label_split) > 1:
            feed_subset = label_split[0].strip()
            feed_category = label_split[1].strip()
        else:
            feed_subset = 'SI'
            feed_category = label_split[0].strip()
        print("crawl_feedly: scraping feed category/title", feed_category, feed_title)
        if rss_field == '' or category_label == rss_field:
            url = "http://cloud.feedly.com/v3/streams/contents"
            params_streams['streamId'] = feed_id
            r = requests.get(url, headers=headers, params=params_streams)
            stream = r.json()
            if 'items' in stream:
                bulk_data = None
                bulk_data = []
                for entry in stream['items']:
                    feedlymap = models.FeedlyMap()
                    feedlymap.post_id = entry['id']
                    feedlymap.url = ""
                    try:
                        feedlymap.published_date = datetime.fromtimestamp(entry['published']/1000)
                    except:
                        last_year = datetime.now().year - 1
                        feedlymap.published_date = datetime(last_year, 1, 1, 00, 00, 00)
                    feedlymap.subset = feed_subset
                    feedlymap.category = feed_category
                    feedlymap.feed = feed_title
                    if 'topics' in feed:
                        feedlymap.feed_topics = feed['topics']
                    if 'keywords' in entry:
                        feedlymap.body_topics = entry['keywords']
                    if 'title' in entry:
                        feedlymap.title = entry['title']
                    if 'canonicalUrl' in entry:
                        feedlymap.url = entry['canonicalUrl']
                    if len(feedlymap.url) == 0:
                        if 'originId' in entry:
                            n = entry['originId'].find('http')
                            if n > 0:
                                feedlymap.url = entry['originId'][n:]
                    if len(feedlymap.url) == 0:
                        if 'origin' in entry:
                            origin = entry['origin']
                            feedlymap.url = origin['htmlUrl']
                    feedlymap.post_id = feedlymap.url
                    if 'summary' in entry:
                        bs = BeautifulSoup(entry['summary']['content'],  "lxml") # in case of RSS feed
                    if 'content' in entry:
                        bs = BeautifulSoup(entry['content']['content'], "lxml") # in case of Google News feed
                    feedlymap.body = bs.get_text().encode("ascii", 'replace')
                    data = elastic.convert_for_bulk(feedlymap, 'update')
                    bulk_data.append(data)
                bulk(models.client, actions=bulk_data, stats_only=True)
    return True

def export_opml_feedly(opml_filename):
    global headers

    url = "http://cloud.feedly.com/v3/opml"
    r = requests.get(url, headers=headers)
    xml = r.content

    opml_file = 'data/' + opml_filename + '_opml.txt'
    try:
        file = open(opml_file, 'wb')
        pyfile = File(file)
        pyfile.write(xml)
        pyfile.close()
        return True
    except:
        return False


def import_opml_feedly(opml_filename):
    global headers

    opml_file = 'data/' + opml_filename + '_opml.txt'
    try:
        file = open(opml_file, 'rb')
        pyfile = File(file)
        xml = pyfile.read()
        pyfile.close()
    except:
        return False

    url = "http://cloud.feedly.com/v3/opml"
    h2 = headers
    h2['Content-Type'] = 'application/xml'
    r = requests.post(url, headers=headers, data=xml)
    
    return True

