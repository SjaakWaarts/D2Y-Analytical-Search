
import json
import logging

import requests
from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import Index, Search

#class ElasticSearchManager:
#    def __init__(self, customer_domain_name, server):
#        logger.info('Setting up ElasticSearch server on address {}'.format(server), extra=extra)

#        self.cdn = str(customer_domain_name)
#        self.server = server
#        self.client = Elasticsearch(server)
#        # TODO: Get all indices on this server.
#        self.index = 'tmlo'

#    def get_archives(self):
#        """Query ElasticsSearch to return all 'Archief' level files belonging to the input customer domain name.

#        Returns:
#            list (str): A list of IDs of the 'Archief' level files that match the customer domain name.
#        """
#        s, q = self._setup_search()
#        s = s.query('match', **{'Record.Aggregatieniveau': 'Archief'})

#        r = s.execute()

#        return r.hits.hits

#    def get_by_id(self, document_id):
#        """Query ElasticSearch to check if the input ID exists in ElasticSearch.

#        Args:
#            document_id (str): The input 'Identificatiekenmerk' (ID) to search for.

#        Returns:
#            True: If the ID exists on the index.
#            False: If the ID does not exist on the index.
#        """
#        s, q = self._setup_search()
#        s = s.query('match', **{'Identificatiekenmerk.keyword': document_id})

#        r = s.execute()

#        # Determine the response based on the number of items that match the query.
#        num_hits = r.hits.total
#        if num_hits == 0:
#            return None
#        elif num_hits == 1:
#            return r.hits.hits.pop()
#        elif num_hits >= 2:
#            logger.warning('Found more than 1 match in the index, {} is already a duplicate!'.format(document_id),
#                           extra=extra)
#            return r.hits.hits

#    def upload(self, index, id, doc):
#        """Upload a document to a specific index."""
#        # doc.save(using=self.client, index=index)
#        ES_HOSTS = [{'host': 'localhost', 'http_auth': ('elastic', 'changeme')}]
#        headers = {'Content-Type': 'application/json'}
#        # if 'http_auth' in es_host:
#        #    headers['http_auth'] = es_host['http_auth']
#        host = self.server
#        doc_type = '_doc'
#        url = "http://" + host + "/" + index
#        data = json.dumps(doc)
#        # use automatic ID creation
#        r = requests.post(url + "/" + doc_type + "/" + id, headers=headers, data=data)
#        if r.status_code >= 400:
#            logging.error('ES upload failed, error {}.'.format(r.text))
#            status = False
#        else:
#            status = True
#        return status

#    def delete_by_query(self, index, q):
#        headers = {'Content-Type': 'application/json'}
#        host = self.server
#        doc_type = '_doc'
#        url = "http://" + host + "/" + index
#        data = json.dumps(q)
#        r = requests.post(url + "/" + doc_type + "/_delete_by_query", headers=headers, data=data)
#        if r.status_code >= 400:
#            logging.error('ES delete_by_query failed, error {}.'.format(r.text))

#    def search_query(self, index, q, doc_type='_doc'):
#        headers = {'Content-Type': 'application/json'}
#        host = self.server
#        url = "http://" + host + "/" + index
#        data = json.dumps(q)
#        r = requests.post(url + "/" + doc_type + "/_search", headers=headers, data=data)
#        if r.status_code >= 400:
#            logging.error('ES search failed, error {}.'.format(r.text))
#        return r

#    def get_doc(self, index, ES_id):
#        headers = {'Content-Type': 'application/json'}
#        host = self.server
#        doc_type = '_doc'
#        url = "http://" + host + "/" + index
#        r = requests.get(url + "/" + doc_type + "/" + ES_id, headers=headers)
#        if r.status_code >= 400:
#            logging.error('ES get failed, error {}.'.format(r.text))
#        return r

#    def put_doc(self, index, ES_id, data):
#        headers = {'Content-Type': 'application/json'}
#        host = self.server
#        doc_type = '_doc'
#        url = "http://" + host + "/" + index
#        r = requests.put(url + "/" + doc_type + "/" + ES_id, headers=headers, data=data)
#        if r.status_code >= 400:
#            logging.error('ES put failed, error {}.'.format(r.text))
#        return r

#    def update_doc(self, index, ES_id, data):
#        headers = {'Content-Type': 'application/json'}
#        host = self.server
#        doc_type = '_doc'
#        url = "http://" + host + "/" + index
#        r = requests.post(url + "/" + doc_type + "/" + ES_id + "/_update", headers=headers, data=data)
#        if r.status_code >= 400:
#            logging.error('ES update failed, error {}.'.format(r.text))
#        return r

#    def create_new_index(self, index_name, params=None):
#        """Creates a new ElasticSearch index using the input settings and parameters.

#        Args:
#            index_name (str): The index name to pass to ElasticSearch.
#            params (str): JSON formatted string configuring index parameters.

#        Returns:
#            True: If the index creation succeeded.
#            False: If the index already exists.
#        """
#        logger.info('Creating ElasticSearch index with name {}'.format(index_name), extra=extra)

#        index = Index(index_name, using=self.client)
#        try:
#            index.create()
#        except es_exceptions.RequestError as e:
#            if e.error == 'resource_already_exists_exception':
#                logger.warning('An index with name {} already exists on the cluster!'.format(index_name), extra=extra)
#            else:
#                logger.error('An error occurred: {}'.format(e), extra=extra)
#            return False

#        self.index = index
#        return True

#    def update_mapping(self, name, doc_type, body):
#        self.client.indices.put_mapping(index=name, doc_type=doc_type, body=body)

#    def _setup_search(self, filter_organisation=True):
#        """Setup an ElasticSearch 'Search' object and add the customer domain name filter to it. All queries must call
#            this function to ensure all queries are filtered properly.

#        Returns:

#        """
#        q = {
#            "query": {
#                "bool": {
#                    "must": [],
#                    "filter": []
#                }
#            },
#            "aggs": {},
#            "sort": []
#        }
#        s = Search(using=self.client, index=self.index)
#        if filter_organisation:
#            q["query"]["bool"]["filter"].append({'term': {'x-customer-meta-domain': self.cdn}})
#            s = s.filter('term', **{'x-customer-meta-domain': self.cdn})
#        d = s.to_dict()

#        return s, q

#    def get_rel_ids(self, rel_id, rel_ids, workbook):
#        s, search_q = self._setup_search()
#        filter_facets = {}
#        filter_facets['parent_id'] = [rel_id]
#        filter_facets['aggregatieniveau'] = ['archief', 'serie', 'dossier']
#        search_filters = search_q["query"]["bool"]["filter"]
#        self.add_search_filter(search_q, filter_facets, workbook)
#        results = self.search_query('tmlo', search_q)
#        results = json.loads(results.text)
#        hits = results.get('hits', {})
#        hits = hits.get('hits', {})
#        if rel_id not in rel_ids:
#            rel_ids.append(rel_id)
#        for hit in hits:
#            new_rel_id = hit['_source']['Identificatiekenmerk']
#            if new_rel_id not in rel_ids:
#                self.get_rel_ids(new_rel_id, rel_ids, workbook)

def add_search_aggs(search_aggs, workbook):
    for facet, facet_conf in workbook['facets'].items():
        if facet in workbook['filters']:
            field = facet_conf['field']
            if facet_conf['has_keyword']:
                field = field + '.keyword'
            nested = facet_conf['nested']
            search_aggs[facet] = {'terms': {"field": field}}
            terms_agg = {'terms': {"field": field}}
            search_aggs[facet] = add_agg_nesting(field, nested, terms_agg)

def add_search_filter(search_q, filter_facets, workbook):
    search_filters = search_q["query"]["bool"]["filter"]
    search_queries = search_q["query"]["bool"]["must"]
    for facet, facet_conf in workbook['facets'].items():
        if facet in filter_facets:
            if filter_facets[facet] is None:
                continue
            field = facet_conf['field']
            if facet_conf['has_keyword']:
                field = field + '.keyword'
            nested = facet_conf['nested']
            if facet_conf['type'] == 'terms':
                terms = filter_facets[facet]
                if len(terms) == 0:
                    continue
                if type(terms) is not list:
                    terms = [terms]
                terms_filter = {"terms": {field: terms}}
                nested_filter = add_filter_nesting(field, nested, terms_filter)
                search_filters.append(nested_filter)
            elif facet_conf['type'] == 'text':
                if filter_facets[facet] in [None, ""]:
                    continue
                q = filter_facets[facet]
                search_queries.append({"query_string": {
                    "query": q, "default_operator": "AND", "fields": [facet_conf['field']]}})
            elif facet_conf['type'] == 'date':
                date_range = filter_facets[facet]
                if date_range in [None, ""]:
                    continue
                date_range_filter = {"range": {field: {}}}
                date_range_filter['range'][field]['gte'] = date_range
                nested_filter = add_filter_nesting(field, nested, date_range_filter)
                search_filters.append(nested_filter)
            elif facet_conf['type'] == 'period':
                date_range = filter_facets[facet]
                if date_range['start'] in [None, ""] and date_range['end'] in [None, ""]:
                    continue
                field = field = facet_conf['field']
                date_range_filter = {"range": {field: {}}}
                if date_range['start'] not in [None, ""]:
                    date_range_filter['range'][field]['gte'] = date_range['start']
                    nested_filter = add_filter_nesting(field, nested, date_range_filter)
                    search_filters.append(nested_filter)
                field = field = facet_conf['field']
                date_range_filter = {"range": {field: {}}}
                if date_range['end'] not in [None, ""]:
                    date_range_filter['range'][field]['lte'] = date_range['end']
                    nested_filter = add_filter_nesting(field, nested, date_range_filter)
                    search_filters.append(nested_filter)
            elif facet_conf['type'] == 'path':
                path = filter_facets[facet]
                if len(path) == 0:
                    continue
                rel_id = path[-1]
                mode = workbook.get('top_down_mode', 'td0')
                if mode == 'td0':
                    search_filters.append({'nested': {'path': 'Relaties',
                                                        'query': {'terms': {field: [rel_id]}}}})
                elif mode == 'td1':
                    # Add a boolean should in the filter context. The document should match the selected id
                    # or it should have a relation to this id.
                    search_filters.append(
                        {
                            "bool": {
                                "should": [
                                    {"term": {"Identificatiekenmerk.keyword": rel_id}},
                                    {"nested": {
                                        "path": "Relaties",
                                        "query": {
                                            "bool": {
                                                "must": [{"terms": {"Relaties.ID": [rel_id]}}]
                                            }
                                        }
                                    }
                                    }
                                ]
                            }
                        }
                    )
                elif mode == 'tdn':
                    rel_ids = [rel_id]  # routine to find all relation id's
                    self.get_rel_ids(rel_id, rel_ids, workbook)
                    search_filters.append({'nested': {'path': 'Relaties',
                                                        'query': {'terms': {field: rel_ids}}}})

def add_agg_nesting(field, nested_field, aggregation):
    nested = {}
    sub_nested = nested
    sub_nested_field = ''
    if nested_field:
        fields = nested_field.split('.')
        for field in fields:
            if sub_nested_field == '':
                sub_nested_field = field
            else:
                sub_nested_field = sub_nested_field + '.' + field
            sub_nested['nested'] = {'path': sub_nested_field}
            sub_nested['aggs'] = {sub_nested_field: {}}
            if field != fields[-1]:
                sub_nested = sub_nested['aggs'][sub_nested_field]
        sub_nested['aggs'][sub_nested_field] = aggregation
    else:
        nested = aggregation
    return nested

def add_filter_nesting(field, nested_field, filter):
    nested_filter = {}
    sub_nested_filter = nested_filter
    sub_nested_field = ''
    if nested_field:
        fields = nested_field.split('.')
        for field in fields:
            if sub_nested_field == '':
                sub_nested_field = field
            else:
                sub_nested_field = sub_nested_field + '.' + field
            sub_nested_filter['nested'] = {'path': sub_nested_field, 'query': {}}
            if field != fields[-1]:
                sub_nested_filter = sub_nested_filter['nested']['query']
        sub_nested_filter['nested']['query'] = filter
    else:
        nested_filter = filter
    return nested_filter

def get_buckets_nesting(field, nested_field, buckets):
    nested_totals = []
    nested_buckets = buckets
    sub_nested_field = ''
    if nested_field:
        fields = nested_field.split('.')
        for field in fields:
            if sub_nested_field == '':
                sub_nested_field = field
            else:
                sub_nested_field = sub_nested_field + '.' + field
            nested_totals.append((sub_nested_field, nested_buckets.get('doc_count', 0)))
            nested_buckets = nested_buckets[sub_nested_field]
    else:
        nested_buckets = buckets
    return nested_buckets['buckets'], nested_totals

def get_field_nesting(nested_field, hit, default_field_value):
    field_value = hit['_source']
    fields = nested_field.split('.')
    for field in fields[:-1]:
        if field in field_value:
            field_value = field_value[field]
            if type(field_value) is list:
                if len(field_value) > 0:
                    field_value = field_value[0]
                else:
                    field_value = {}
        else:
            field_value = {}
            break
    field = fields[-1]
    if field in field_value:
        field_value = field_value[field]
    else:
        field_value = default_field_value
    return field_value

def get_bucket_value_nesting(nested_field, bucket):
    sub_bucket = bucket
    fields = nested_field.split('.')
    sub_nested_field = ''
    for field in fields:
        if sub_nested_field == '':
            sub_nested_field = field
        else:
            sub_nested_field = sub_nested_field + '.' + field
        if sub_nested_field in sub_bucket:
            sub_bucket = sub_bucket[sub_nested_field]
            if type(sub_bucket) is list:
                if len(sub_bucket) > 0:
                    sub_bucket = sub_bucket[0]
                else:
                    sub_bucket = {}
        else:
            sub_bucket = {}
            break
    if 'value' in sub_bucket:
        field_value = sub_bucket['value']
    else:
        field_value = None
    return field_value


def delete_by_query(es_host, index, q, doc_type=None):
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    if doc_type is None:
        doc_type = index
    url = "http://" + host + ":9200" + "/" + index
    data = json.dumps(q)
    r = requests.post(url + "/_delete_by_query", headers=headers, data=data)
    if r.status_code >= 400:
        logging.error('ES delete_by_query failed, error {}.'.format(r.text))
    return r

def setup_search():
    q = {
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        },
        "aggs": {},
        "sort": []
    }
    s = Search()
    return s, q

def search_query(es_host, index, q):
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200" + "/" + index
    data = json.dumps(q)
    r = requests.post(url + "/_doc/_search", headers=headers, data=data)
    if r.status_code >= 400:
        logging.error('ES search failed, error {}.'.format(r.text))
    return r

def create_doc(es_host, index, id, doc):
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200" + "/" + index
    data = json.dumps(doc)
    r = requests.post(url + "/_doc/" + id + "/_create", headers=headers, data=data)
    if r.status_code >= 400:
        logging.error('ES creation failed, error {}.'.format(r.text))
    return r

def get_doc(es_host, index, id):
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200" + "/" + index
    r = requests.get(url + "/_doc/" + id, headers=headers)
    if r.status_code >= 400:
        logging.error('ES get failed for {}, error {}.'.format(id, r.text))
    return r

def put_doc(es_host, index, id, doc):
    headers = {'Content-Type': 'application/json'}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    url = "http://" + host + ":9200" + "/" + index
    data = json.dumps(doc)
    r = requests.put(url + "/_doc/" + id, headers=headers, data=data)
    if r.status_code >= 400:
        logging.error('ES put failed, error {}.'.format(r.text))
    return r
