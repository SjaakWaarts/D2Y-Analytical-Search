
from datetime import datetime
from dateutil import parser as dateparser
import time
from string import ascii_lowercase as ALC
import itertools
from django.core.files import File
from django.views.generic.base import TemplateView
import glob, os
import pickle
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import urllib
from urllib.parse import urlencode
from copy import deepcopy
import requests
from lxml import html
from bs4 import BeautifulSoup
import json
import re

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import seeker
import app.models as models
import app.elastic as elastic
import app.sentiment as sentiment

###
### Product Back-End Routines: from data structure to JSON file and from JSON file to ElasticSearch Index
###

def save_products_data(product):
    json_file = 'data/' + product + '_products.json'
    try:
        file = open(json_file, 'w')
        pyfile = File(file)
        json.dump(models.scrape_li, pyfile)
        pyfile.close()
        return True
    except:
        return False

def retrieve_products_data(product):
    json_file = 'data/' + product + '_products.json'
    try:
        file = open(json_file, 'r')
        pyfile = File(file)
        models.scrape_li = json.load( pyfile)
        pyfile.close()
        return True
    except:
        return False

def scrape_save(product):
    ml_file = 'data/' + product + '_scrape.pickle'
    try:
        file = open(ml_file, 'wb')
        pyfile = File(file)
        pickle.dump(models.scrape_li, pyfile, protocol=pickle.HIGHEST_PROTOCOL)
        pyfile.close()
        return True
    except:
        return False

def scrape_retrieve(brand_name, brand_variant, product):
    # Read old format
    ml_file = 'data/' + product + '_scrape.pickle'
    try:
        file = open(ml_file, 'rb')
        pyfile = File(file)
        models.scrape_li = pickle.load(pyfile)
        pyfile.close()
        #return True
    except:
        return False
    # Convert to the new format
    products_data = []
    for scrape_perfume in models.scrape_li:
        review_count =1
        reviews = []
        scrape_reviews = scrape_perfume[1][4]
        for scrape_review in scrape_reviews:
            review = models.Review()
            review.reviewid = scrape_perfume[1][0] + "?review=" + str(review_count)
            review_count = review_count + 1
            review.perfume = scrape_perfume[0]
            review.review_date = scrape_review[0]
            review.review = scrape_review[1]
            review.label = scrape_review[2]
            review.accords = scrape_perfume[1][1]
            review.img_src = scrape_perfume[1][5]
            reviews.append({
                'date'      : review.review_date,
                'body'      : review.review,
                'label'     : review.label,
                })
        product_data = {
            'site'      : "Fragrantica",
            'brand_name': brand_name,
            'brand_variant' : brand_variant,
            'perfume'   : review.perfume,
            'img_src'   : review.img_src,
            'price'     : 0.0,
            'ratings'   : {},
            'accords'   : review.accords,
            'reviews'   : reviews,
            'url'       : scrape_perfume[1][0],
            }
        products_data.append(product_data)
    models.scrape_li = products_data
    # Write new format
    json_file = 'data/' + product + '_products.json'
    try:
        file = open(json_file, 'w')
        pyfile = File(file)
        json.dump(models.scrape_li, pyfile)
        pyfile.close()
        return True
    except:
        return False

def index_products_data():
    count = 1
    data = []
    for product_data in models.scrape_li:
        review_count =1
        reviews = product_data['reviews']
        for review in reviews:
            r = models.Review()
            r.reviewid = product_data['url'] + "?review=" + str(review_count)
            review_count = review_count + 1
            r.perfume = product_data['perfume']
            r.site = product_data['site']
            r.brand_name = product_data['brand_name']
            r.brand_variant = product_data['brand_variant']
            r.review_date = datetime.strptime(review['date'],'%b %d %Y').date()
            r.review = review['body']
            r.label = review['label']
            r.accords = product_data.get('accords', {})
            r.img_src = product_data.get('img_src', "")
            if count < 100:
                data.append(elastic.convert_for_bulk(r, 'update'))
            count = count + 1
    bulk(models.client, actions=data, stats_only=True)

###
### FRAGRANTICA
###

def scrape_fragrantica_search_product(product, perfumes, designers):
    global driver

    driver.get("http://www.fragrantica.com/")
    #qajax = driver.find_element_by_id("qajax")
    qajax = driver.find_element_by_id("super-search")
    #qajax.clear()
    qajax.send_keys(product)
    time.sleep(3)
    presultsajax = driver.find_element_by_id("presultsajax")
    perfume_a_tags = presultsajax.find_elements_by_tag_name("a")
    for perfume_a_tag in perfume_a_tags:
        pname = perfume_a_tag.text
        purl = perfume_a_tag.get_attribute('href')
        perfumes[pname] = purl
    dresultsajax = driver.find_element_by_id("dresultsajax")
    designer_a_tags = dresultsajax.find_elements_by_tag_name("a")
    for designer_a_tag in designer_a_tags:
        dname = designer_a_tag.text
        durl = designer_a_tag.get_attribute('href')
        designers[dname] = durl

def scrape_fragrantica_product(brand_name, brand_variant, perfume, purl):
    global driver

    accords = {}
    votes = {}
    notes = {}
    longevity = []
    sillage = []
    also_likes = []
    reviews = []
    reminds_me_of = []

# <div id="prettyPhotoGallery">
#   <div>
#       <div> <span> Main Accords </span></div>
#       <div> <span> Accord </span> <div style="width": 99px></div> </div>
#       <div style="clear: both;"> </div>

    try:
        driver.get(purl)
        msg = "scraping page %s" % (purl)
        print (msg)
#       models.scrape_q.put(msg)
    except:
        msg = "page could not be scraped %s" % (purl)
        print (msg)
#       models.scrape_q.put(msg)
        return

    # Image
    try:
        mainpicbox = driver.find_element_by_id("mainpicbox")    
        img_tag = mainpicbox.find_element_by_tag_name("img")
        #img_src = 'src=' + img_tag.get_attribute('src')
        img_src = img_tag.get_attribute('src')
    except:
        img_src = ''
        pass

    # Accords
    try:
        prettyPhotoGallery = driver.find_element_by_id("prettyPhotoGallery")    
        accord_div_tags = prettyPhotoGallery.find_element_by_tag_name("div").find_elements_by_tag_name("div")
        accord_span_tags = prettyPhotoGallery.find_element_by_tag_name("div").find_elements_by_tag_name("span")
        if len(accord_span_tags) > 0:
            for i in range(1, len(accord_span_tags)):
                accord_span_tag = accord_span_tags[i]
                accord_div_tag = accord_div_tags[i*3-1]
                aname = accord_span_tag.text
                width = accord_div_tag.size['width']
                width2 = accord_div_tag.get_attribute('style').split(';')[0].split(':')[1]
                accords[aname] = width
    except:
        pass
    if len(accords) == 0:
        accords['NONE'] = 1

    # Moods
    try:
        statusDivs_tag = driver.find_element_by_id("statusDivs")
        vote_div_tags = statusDivs_tag.find_elements_by_class_name("votecaption")
        diagramresult_tag = driver.find_element_by_id("diagramresult")
        result_div_tags = diagramresult_tag.find_elements_by_tag_name("div")
        for i in range(0, len(vote_div_tags)):
            vname = vote_div_tags[i].text
            height = result_div_tags[i].size['height']
            votes[vname] = height

    #       votes['total'] = int(driver.find_element_by_id("peopleD").text)
    #       votes['rating avg'] = float(driver.find_element_by_xpath("//span[@itemprop='ratingValue']").text)
    #       votes['rating best'] = float(driver.find_element_by_xpath("//span[@itemprop='bestRating']").text)
    except:
        pass
    if len(votes) == 0:
        votes['NONE'] = 1

    # Notes
    try:
        userMainNotes_tag = driver.find_element_by_id("userMainNotes")
        note_img_tags = userMainNotes_tag.find_elements_by_tag_name("img")
        note_span_tags = userMainNotes_tag.find_elements_by_tag_name("span")
        total_note_votes = 0
        for i in range(0, len(note_img_tags)):
            nname = note_img_tags[i].get_attribute('title')
            note_votes = int(note_span_tags[i].text)
            notes[nname] = note_votes
            total_note_votes = total_note_votes + note_votes
#        notes['total'] = total_note_votes
    except:
        pass
    if len(notes) == 0:
        notes['NONE'] = 1

    # Reviews
    try:
        revND_tags = driver.find_elements_by_class_name("revND")
        dateND_tags = driver.find_elements_by_class_name("dateND")
        for i in range(0, len(revND_tags)):
            review_text = revND_tags[i].text
            review_date = dateND_tags[i].get_attribute('textContent').rstrip()
            reviews.append({
                'date'      : review_date,
                'body'      : review_text,
                'label'     : 'init',
                })
    except:
        pass


    product_data = {
        'site'      : "Fragrantica",
        'brand_name': brand_name,
        'brand_variant' : brand_variant,
        'perfume'   : perfume,
        'img_src'   : img_src,
        'price'     : 0.0,
        'ratings'   : {},
        'accords'   : accords,
        'votes'     : votes,
        'notes'     : notes,
        'reviews'   : reviews,
        'url'       : purl,
        }
    return product_data

def crawl_fragrantica_data(brand_name, brand_variant, perfume_name):
    global driver

    products_data = []
    perfumes = {}
    designers = {}
    url = 'https://www.fragrantica.com/search/?q='+perfume_name
    # use headers to mimic a true browser instead of a bot
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    # DRIVER APPROACH IS NEEDED SINCE CONTENT IS GENERATED BY JavaScript, SEARCH PAGE CAN BE USED DIRECTLY WITH BS (OR PARSER)
    # 1. DRIVER APPROACH
    #driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(chrome_options=options)
    #driver = webdriver.Chrome()
    driver.get(url)
    # the hits of the driver are of type WebElement
    #hits = driver.find_elements_by_xpath("//div[contains(@class,'ais-infinite-hits')]/div[contains(@class,'ais-infinite-hits--item')")
    #hits = driver.find_elements_by_xpath("//div[contains(@class,'ais-infinite-hits')]/div")
    #page = driver.page_source
    #parser = html.fromstring(page)
    # 2. PARSER APPROACH
    #page = requests.get(url, headers = headers)
    #parser = html.fromstring(page.content)
    # the hits of the partser are of type HtmlElement, this is better as WebElement
    #hits = parser.xpath("//div[contains(@class,'ais-infinite-hits')]/div[contains(@class,'ais-infinite-hits--item')")
    #hits = parser.xpath("//div[contains(@class,'ais-infinite-hits')]/div")
    # 3. OLD DRIVER APPROACH
    #scrape_fragrantica_search_product(perfume_name, perfumes, designers)
    # 4. BS APPROACH, with the new nameing conventions find_
    #req = urllib.request.Request(url, headers=headers)
    #req_open = urllib.request.urlopen(req)
    #bs = BeautifulSoup(req_open.read(), "lxml")

    bs = BeautifulSoup(driver.page_source, "lxml")
    hits = bs.find_all("div", class_="ais-infinite-hits--item")
    for hit in hits:
        #perfume_a_tags = hit.find_elements_by_tag_name("a")
        perfume_a_tag = hit.find("a")
        pname = perfume_a_tag.parent.text
        #purl = perfume_a_tag.get_attribute('href')
        purl = perfume_a_tag.attrs['href']
        perfumes[pname] = purl
    for perfume, purl in perfumes.items():  
        products_data.append(scrape_fragrantica_product(brand_name, brand_variant, perfume, purl))
    return products_data


def crawl_fragrantica(brand_name, brand_variant, perfume_name):
    models.scrape_li = None
    success = False
    perfumes = {}
    designers = {}
    models.scrape_li = crawl_fragrantica_data(brand_name, brand_variant, perfume_name)
    sentiment.sentiment(perfume_name)
    success = save_products_data(perfume_name)


def retrieve_fragrantica(brand_name, brand_variant, perfume_name):
    models.scrape_li = None
    success = False
    #if scrape_retrieve(brand_name, brand_variant, perfume_name):
    if retrieve_products_data(perfume_name):
        index_products_data()
        success = True
    return success

###
### AMAZON
###

def crawl_amazon_data(brand_name, brand_variant, asin):
    #This script has only been tested with Amazon.com
    #amazon_url  = 'http://www.amazon.com/dp/'+asin
    amazon_url = 'http://www.amazon.com/review/product/'+asin+'/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8&filterByStar=all_stars&reviewerType=all_reviews&sortBy=recent&pageNumber=1'
    # Add some recent user agent to prevent amazon from blocking the request 
    # Find some chrome user agent strings  here https://udger.com/resources/ua-list/browser-detail?browser=Chrome
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
    page = requests.get(amazon_url,headers = headers)

    parser = html.fromstring(page.content)
    XPATH_AGGREGATE = '//span[@id="acrCustomerReviewText"]'
    XPATH_REVIEW_SECTION = '//div[@id="cm_cr-review_list"]/div[contains(@class,"review")]'
    XPATH_AGGREGATE_RATING = '//table[@id="histogramTable"]//tr'
    #XPATH_PRODUCT_NAME = '//h1//span[@id="productTitle"]//text()'
    XPATH_PRODUCT_NAME = '//div[contains(@class,"product-title")]//text()'
    XPATH_PRODUCT_IMAGE = '//div[contains(@class,"product-image")]/a/img/@src'
    XPATH_PRODUCT_PRICE  = '//span[@id="priceblock_ourprice"]/text()'

    raw_product_price = parser.xpath(XPATH_PRODUCT_PRICE)
    product_price = ''.join(raw_product_price).replace(',','')

    raw_product_name = parser.xpath(XPATH_PRODUCT_NAME)
    product_name = ''.join(raw_product_name).strip()
    raw_product_image = parser.xpath(XPATH_PRODUCT_IMAGE)
    product_image = ''.join(raw_product_image).strip()
    total_ratings  = parser.xpath(XPATH_AGGREGATE_RATING)
    reviews = parser.xpath(XPATH_REVIEW_SECTION)

    ratings_dict = {}
    reviews_list = []

    #grabing the rating  section in product page
    for ratings in total_ratings:
        extracted_rating = ratings.xpath('./td//a//text()')
        if extracted_rating:
            rating_key = str(extracted_rating[0])
            raw_raing_value = str(extracted_rating[1])
            rating_value = raw_raing_value
            if rating_key:
                ratings_dict.update({rating_key:rating_value})

    #Parsing individual reviews
    for review in reviews:
        #XPATH_REVIEW_AUTHOR  = './/a[contains(@href,"/profile/")]/parent::span//text()'
        #XPATH_RATING  ='./div//div//i//text()'
        #XPATH_REVIEW_HEADER = './div//div//span[contains(@class,"text-bold")]//text()'
        #XPATH_REVIEW_POSTED_DATE = './/a[contains(@href,"/profile/")]/parent::span/following-sibling::span/text()'
        #XPATH_REVIEW_VOTES = './/a[contains(@class,"commentStripe")]/text()'
        XPATH_REVIEW_AUTHOR  = './/a[contains(@class,"author")]//text()'
        XPATH_REVIEW_RATING  = './/i[contains(@class,"review-rating")]//text()'
        XPATH_REVIEW_TITLE = './/a[contains(@class,"review-title")]//text()'
        XPATH_REVIEW_DATE = './/span[contains(@class,"review-date")]//text()'
        XPATH_REVIEW_TEXT = './/div//span[contains(@class,"review-text")]//text()'
        XPATH_REVIEW_VOTES = './/span[contains(@class,"review-votes")]/text()'

        raw_review_author = review.xpath(XPATH_REVIEW_AUTHOR)
        raw_review_rating = review.xpath(XPATH_REVIEW_RATING)
        raw_review_title = review.xpath(XPATH_REVIEW_TITLE)
        raw_review_date = review.xpath(XPATH_REVIEW_DATE)
        raw_review_text = review.xpath(XPATH_REVIEW_TEXT)
        #cleaning data
        review_author = str(raw_review_author[0])
        review_rating = str(raw_review_rating[0]).replace('out of 5 stars','')
        review_title = ' '.join(' '.join(raw_review_title).split())
        review_date = ''.join(raw_review_date).replace('on ','')
        review_date = datetime.strptime(review_date, '%B %d, %Y').date()
        review_date = review_date.strftime('%b %d %Y') # mmm dd YYYY normalized date format
        review_text = ' '.join(' '.join(raw_review_text).split())

        raw_review_comments = review.xpath(XPATH_REVIEW_VOTES)
        review_comments = ' '.join(raw_review_comments)
        review_comments = re.sub('[A-Za-z]','',review_comments).strip()
        review = {
            'date'  : review_date,
            'body'   : review_text,
            'label'  : 'init'
            }
        reviews_list.append(review)

    product_data = {
        'site'      : "Amazon",
        'brand_name': brand_name,
        'brand_variant' : brand_variant,
        'perfume'   : product_name,
        'img_src'   : product_image,
        'price'     : product_price,
        'ratings'   : ratings_dict,
        'reviews'   : reviews_list,
        'url'       : amazon_url,
        }
    #scrape_li = [(product_name, [amazon_url, {}, {}, {}, reviews_list, product_image])]
    return product_data


def crawl_amazon(brand_name, brand_variant, asin):
    # ASIN is Amazon Standard Identification Number
    models.scrape_li = None
    success = False
    print("Downloading and processing page http://www.amazon.com/review/product/"+asin)
    product_data = crawl_amazon_data(brand_name, brand_variant, asin)
    models.scrape_li = [product_data]
    success = save_products_data(asin)
    return success


def retrieve_amazon(asin):
    models.scrape_li = None
    success = False
    if retrieve_products_data(asin):
        index_products_data()
        success = True
    return success


###
### Product Elastic View
###


class ProductElasticView(TemplateView):

    template_name = "app/product_elastic.html"
    facets = {
        "perfume" : "perfume.keyword",
        "label"   : "label.keyword",
        "accords" : "accords.accord.keyword"
        }
    kfs = ("bottle", "floral")

    def get_context_data(self, *args, **kwargs):
        es_query, search_value, kfs = self.gen_es_query(self.request)
        if len(kfs) == 0:
            kfs = ProductElasticView.kfs

        body = {'aggs' : {} }
        for facet_key, facet_field in ProductElasticView.facets.items():
            body['aggs'][facet_key] = {'terms' : {'field' : facet_field}}

        body_kf = {}
        for kf in kfs:
            body_kf[kf] = {'match' : {'review': kf}}
        body['aggs']['review'] = {'filters': {'filters': body_kf }}
        body.update({'query': es_query})

        search_result = models.client.search(index='review', doc_type='perfume', body=body)

        context = super(ProductElasticView, self).get_context_data(**kwargs)
        context['search'] = search_value
        context['kfs'] = ",".join(kfs)
        context['hits'] = [
            self.convert_hit_to_template(c) for c in search_result['hits']['hits']
        ]
        context['aggregations'] = self.prepare_facet_data(
            search_result['aggregations'],
            self.request.GET
        )
        return context

    def convert_hit_to_template(self, hit1):
        hit = deepcopy(hit1)
        almost_ready = hit['_source']
        almost_ready['pk'] = hit['_id']
        return almost_ready

    def facet_url_args(self, url_args, field_name, field_value):
        if field_name in ProductElasticView.facets:
            field_name = ProductElasticView.facets[field_name]
        is_active = False
        if url_args.get(field_name):
            base_list = url_args[field_name].split(',')
            if field_value in base_list:
                del base_list[base_list.index(field_value)]
                is_active = True
            else:
                base_list.append(field_value)
            url_args[field_name] = ','.join(base_list)
        else:
            url_args[field_name] = field_value
        return url_args, is_active

    def prepare_facet_data(self, aggregations_dict, get_args):
        resp = {}
        for area in aggregations_dict.keys():
            resp[area] = []
            if area == 'age':
                resp[area] = aggregations_dict[area]['buckets']
                continue
            for item in aggregations_dict[area]['buckets']:
                if isinstance(item, str): # review
                    key = item
                    doc_count = aggregations_dict[area]['buckets'][item]['doc_count']
                else:
                    key = item['key']
                    doc_count = item['doc_count']
                url_args, is_active = self.facet_url_args(
                    url_args=deepcopy(get_args.dict()),
                    field_name=area,
                    field_value=key
                )
                resp[area].append({
                    'url_args': urlencode(url_args),
                    'name': key,
                    'count': doc_count,
                    'is_active': is_active
                })
        return resp

    def gen_es_query(self, request):
        es_query = {'match_all': {}}
        search_value = "*"
        kfs = ()
        req_dict = deepcopy(request.GET.dict())
        if not req_dict:
            return es_query, search_value, kfs
        filters = []
        for field_name in req_dict.keys():
            if field_name == 'search':
                search_value = req_dict[field_name]
            elif field_name == 'kfs':
                kfs = req_dict[field_name].split(',')
            else:
                if '__' in field_name:
                    filter_field_name = field_name.replace('__', '.')
                else:
                    filter_field_name = field_name
                for field_value in req_dict[field_name].split(','):
                    if not field_value:
                        continue
                    filters.append(
                        {
                            'term': {filter_field_name: field_value}
                        }
                    )
        es_query = {
            'bool': {
                'must' : {
                    'query_string': {'query': search_value},
                    },
                'filter': {
                    'bool': {
                        'must': filters
                    }
                }
            }
        }
        return es_query, search_value, kfs

