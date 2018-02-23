
from datetime import datetime
import requests
from requests_ntlm import HttpNtlmAuth
from requests.auth import HTTPBasicAuth
import json

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
import seeker
import app.models as models
from FMI.settings import BASE_DIR, ES_HOSTS

#from elasticsearch_dsl import DocType, String, Date, Double, Long, Integer

#class Account(DocType):
#    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
#    body = String(analyzer='snowball')
#    tags = String(index='not_analyzed')
#    published_from = Date()
#    account_number = Long()
#    address = String()
#    age = Long()
#    balance = Long()
#    city = String()
#    employer = String()
#    firstname = String()
#    gender = String()
#    lastname = String()
#    state = String()


def elastic_bank():
    s = Search(using=models.client, index="bank") \
        .query("match_all")
    response = s.execute()
    for hit in response:
        print(hit.meta.score, hit.lastname)

#    models.AccountMappingDoc.init(index="bank", using=models.client)
#    account1 = models.AccountMappingDoc.get(id=1, using=models.client, index="bank")
#    s = models.AccountMappingDoc.search()
#    s = s.query("match", gender="F")
#    s = s.query("match_all")
#    accounts = s.execute()
#    for account in accounts:
#        print(account.meta.score, account.lastname)
#    pass


def elastic_seeker1():
    BookDoc = seeker.document_from_model(models.Book, index="seeker-tests", using=models.client)
    seeker.register(BookDoc)
    s = BookDoc.search()
    s = s.query("match_all")
    books = s.execute()
    for book in books:
        print(book.meta.score, book.authors)
    models.BookDoc = BookDoc

def elastic_seeker2():
#    models.BookDoc = seeker.document_from_model(models.Book, index="seeker-tests", using=models.client)
#    seeker.register(models.BookDoc)
    s = models.BookDoc.search().index("seeker-tests").using(models.client).extra(track_scores=True)
    s = s.query("match_all")
    books = s.execute()
    for book in books:
        print(book.meta.score, book.authors)

def elastic_review():
    s = models.PerfumeDoc.search().index("review").using(models.client).extra(track_scores=True)
    s = s.query("match_all")
    reviews = s.execute()
    for review in reviews:
        print(review.meta.score, review.perfume)

def sharepoint_bi():
    headers = {'accept': 'application/json;odata=verbose'}
    user = 'GLOBAL\\abc1234'
    pswrd = 'xxxxxx'
    url =  'https://teamsites.iff.com/corporate/it/AppDev/BI/_api/web/'

#    r = requests.get("https://teamsites.iff.com/_api/web/title", auth=HTTPBasicAuth(user, pswrd), headers=headers)
#    r = requests.get("https://teamsites.iff.com/_api/web/title", auth=HttpNtlmAuth(user, pswrd), headers=headers)
#    r = requests.get("https://teamsites.iff.com/_api/web/lists", auth=HttpNtlmAuth(user, pswrd), headers=headers)
#    r = requests.get(url + "lists/getByTitle('SalesRepComments')/fields", auth=HttpNtlmAuth(user, pswrd), headers=headers)
    r = requests.get(url + "lists/getByTitle('SalesRepComments')/items", auth=HttpNtlmAuth(user, pswrd), headers=headers)
    select = "$select=SalesRep,Comment"
    filter = "$filter=Cycle eq '009.2012'"
    r = requests.get(url + "lists/getByTitle('SalesRepComments')/items?" + select + filter, auth=HttpNtlmAuth(user, pswrd), headers=headers)
    j = r.json()

    print( r.status_code)
    print (r.content)


def sharepoint_mi():
    headers = {'accept': 'application/json;odata=verbose'}
    user = 'GLOBAL\\abc1234'
    pswrd = 'xxxxxx'
    url =  'https://iffconnect.iff.com/Fragrances/marketintelligence/_api/web/'

#    r = requests.get(url + "title", auth=HttpNtlmAuth(user, pswrd), headers=headers)
#    r = requests.get(url + "lists?$select=EntityTypeName", auth=HttpNtlmAuth(user, pswrd), headers=headers)
#    r = requests.get(url + "lists/getByTitle('Posts')/fields", auth=HttpNtlmAuth(user, pswrd), headers=headers)
    r = requests.get(url + "lists/getByTitle('Posts')/items", auth=HttpNtlmAuth(user, pswrd), headers=headers)
#    select = "$select=SalesRep,Comment"
#    filter = "$filter=Cycle eq '009.2012'"
#    r = requests.get(url + "lists/getByTitle('Posts')/items?" + select + filter, auth=HttpNtlmAuth(user, pswrd), headers=headers)
    j = r.json()

    print( r.status_code)
    print (r.content)

def elastic_api(index, query_string, filters, aggregates):
    post_header = index + "/_search"
    post_match = {"query" : {"match" : {"_all" : q }}}
    post_filters = {}
    for filter_field, filter_value in filters.iteritems():
        post_filter = {"query" : {"term" : {filter_field : filter_value}}}
        j = j + json.dumps(post_filter)
    for aggr_field, agg_type in aggregates.iteritems():
        aggr = {"aggs" : {aggr_field : {aggr_type : {"field" : aggr_field}}}}
        j = j + json.dumps(aggr)


def elastic_py():
    #response = client.search(
    #    index="my-index",
    #    body={
    #      "query": {
    #        "filtered": {
    #          "query": {
    #            "bool": {
    #              "must": [{"match": {"title": "python"}}],
    #              "must_not": [{"match": {"description": "beta"}}]
    #            }
    #          },
    #          "filter": {"term": {"category": "search"}}
    #        }
    #      },
    #      "aggs" : {
    #        "per_tag": {
    #          "terms": {"field": "tags"},
    #          "aggs": {
    #            "max_lines": {"max": {"field": "lines"}}
    #          }
    #        }
    #      }
    #    }
    #)
    client = Elasticsearch()
    response = client.search(
        index="bank",
        body={
            "query": { "match_all": {} },
            "sort": [ { "account_number": "asc" } ]
        }
    )

    for hit in response['hits']['hits']:
        print(hit['_score'], hit['_source']['lastname'])


# Same query but using DSL


def elastic_dsl():
    #s = Search(using=client, index="my-index") \
    #    .filter("term", category="search") \
    #    .query("match", title="python")   \
    #    .query(~Q("match", description="beta"))

    #s.aggs.bucket('per_tag', 'terms', field='tags') \
    #    .metric('max_lines', 'max', field='lines')

    s = Search(using=models.client, index="bank") \
        .query("match_all")

    response = s.execute()

    for hit in response:
        print(hit.meta.score, hit.lastname)

    s = Search(using=models.client, index="bank") \
        .filter("term", state="TX") \
        .query("match_all")

    response = s.execute()

    for hit in response:
        print(hit.meta.score, hit.lastname)


# Define a default Elasticsearch client
#connections.create_connection(hosts=['localhost'])

#class Article(DocType):
#    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
#    body = String(analyzer='snowball')
#    tags = String(index='not_analyzed')
#    published_from = Date()
#    lines = Integer()

#    class Meta:
#        index = 'blog'

#    def save(self, ** kwargs):
#        self.lines = len(self.body.split())
#        return super(Article, self).save(** kwargs)

#    def is_published(self):
#        return datetime.now() < self.published_from

## create the mappings in elasticsearch
#Article.init()

## create and save and article
#article = Article(meta={'id': 42}, title='Hello world!', tags=['test'])
#article.body = ''' looong text '''
#article.published_from = datetime.now()
#article.save()

#article = Article.get(id=42)
#print(article.is_published())

## Display cluster health
#print(connections.get_connection().cluster.health())


def elastic_get(index, endpoint, params):
    es_host = ES_HOSTS[0]
    headers = {}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200/" + index
    data = json.dumps(params)
    r = requests.get(url + "/" + endpoint + "/" + index, headers=headers, data=data)
    results = json.loads(r.text)
    return results

def elastic_put(index, endpoint, params):
    es_host = ES_HOSTS[0]
    headers = {}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200/" + index
    data = json.dumps(params)
    r = requests.put(url + "/" + endpoint + "/" + index, headers=headers, data=data)

def add_to_bulk(index, doc_type, data, action=None):
    if action == 'create':
        metadata = {
            '_op_type': action,
            "_index": objmap._meta.es_index_name,
            "_type": objmap._meta.es_type_name,
        }
        data.update(**metadata)
        bulk_data = data
    elif action == 'update':
        id = data['_id']
        data.pop('_id', None)
        bulkdata = {
            '_op_type': action,
            "_index": index,
            "_type": doc_type,
            '_id': id,
            "doc_as_upsert" : 'true',
            "doc" : data
        }
    return bulkdata

def convert_for_bulk(objmap, action=None):
    data = objmap.es_repr()
    if action == 'create':
        metadata = {
            '_op_type': action,
            "_index": objmap._meta.es_index_name,
            "_type": objmap._meta.es_type_name,
        }
        data.update(**metadata)
        bulk_data = data
    elif action == 'update':
        id = data['_id']
        data.pop('_id', None)
        bulkdata = {
            '_op_type': action,
            "_index": objmap._meta.es_index_name,
            "_type": objmap._meta.es_type_name,
            '_id': id,
            "doc_as_upsert" : 'true',
            "doc" : data
        }
    return bulkdata


def convert_field(data, field, map, field_value):
    # map: 0=question, 1=answer, 2=column, 3=field_type
    question = map[0]
    answer = map[1]
    field_type = map[3]
    if field_type == 'string':
        if type(field_value) == int:
            field_value = "{0:d}".format(field_value)
        data[field] = field_value
    elif field_type == 'text':
        if type(field_value) == int:
            field_value = "{0:d}".format(field_value)
        data[field] = field_value
    elif field_type == 'integer':
        data[field] = int(float(field_value))
    elif field_type == 'float':
        data[field] = float(field_value)
    elif field_type == 'date':
        data[field] = field_value
        #data[field] = datetime.strptime(field_value,'%Y-%m-%d').date()
    elif field_type == 'dict':
        data[field] = field_value #conversion from answer values to dict already happened
    elif field_type == 'nested_qst_ans':
        if field not in data:
            data[field] = []
        data[field].append({'question': answer, 'answer': field_value})
    elif field_type == 'nested_val_prc':
        if field not in data:
            data[field] = []
        data[field].append({'val':question, 'prc':field_value})


def convert_data_for_bulk(data, es_index, es_type, action=None):
    if action == 'create':
        metadata = {
            '_op_type': action,
            "_index": objmap._meta.es_index_name,
            "_type": objmap._meta.es_type_name,
        }
        data.update(**metadata)
        bulk_data = data
    elif action == 'update':
        id = data['_id']
        data.pop('_id', None)
        bulkdata = {
            '_op_type': action,
            "_index": es_index,
            "_type": es_type,
            '_id': id,
            "doc_as_upsert" : 'true',
            "doc" : data
        }
    return bulkdata
