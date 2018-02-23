
from datetime import datetime
import time
from string import ascii_lowercase as ALC
import itertools
from django.core.files import File
from django.views.generic.base import TemplateView
import glob, os
import pickle
from selenium import webdriver
from urllib.parse import urlencode
from copy import deepcopy
import json

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import seeker
import app.models as models
import app.elastic as elastic
import app.sentiment as sentiment


def scrape_fragrantica_search_product(product, perfumes, designers):
    global driver

    driver.get("http://www.fragrantica.com/")
    qajax = driver.find_element_by_id("qajax")
    qajax.clear()
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

def scrape_fragrantica_product(product, purl):
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
            review = revND_tags[i].text
            date = dateND_tags[i].get_attribute('textContent').rstrip()
            reviews.append([date, review, 'init'])
    except:
        pass

    return [purl, accords, votes, notes, reviews, img_src]

def crawl_fragrantica(product):
    global driver

    scrape_d = {}
    driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe')
    perfumes = {}
    designers = {}
    scrape_fragrantica_search_product(product, perfumes, designers)
    for perfume, purl in perfumes.items():  
        scrape_d[perfume] = scrape_fragrantica_product(perfume, purl)
    return list(scrape_d.items())

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

def scrape_retrieve(product):
    brand_field = product
    ml_file = 'data/' + brand_field + '_scrape.pickle'
    try:
        file = open(ml_file, 'rb')
        pyfile = File(file)
        models.scrape_li = pickle.load(pyfile)
        pyfile.close()
        return True
    except:
        return False


def push_review_to_index():
    count = 1
    data = []
    for scrape_perfume in models.scrape_li:
        review_count =1
        scrape_reviews = scrape_perfume[1][4]
        for scrape_review in scrape_reviews:
            review = models.Review()
            review.reviewid = scrape_perfume[1][0] + "?review=" + str(review_count)
            review_count = review_count + 1
            review.perfume = scrape_perfume[0]
            review.review_date = datetime.strptime(scrape_review[0],'%b %d %Y').date()
            review.review = scrape_review[1]
            review.label = scrape_review[2]
            review.accords = scrape_perfume[1][1]
            review.img_src = scrape_perfume[1][5]
            if count < 100:
                data.append(elastic.convert_for_bulk(review, 'update'))
            count = count + 1

    bulk(models.client, actions=data, stats_only=True)


def crawl_product(index_choices, product):
    models.scrape_li = None
    success = False
    perfumes = {}
    designers = {}
    models.scrape_li = crawl_fragrantica(product)
    sentiment.sentiment(product)
    success = scrape_save(product)


def index_product(index_choices, product):
    models.scrape_li = None
    success = False
    perfumes = {}
    designers = {}
    if scrape_retrieve(product):
        push_review_to_index()
        success = True
    return success


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







