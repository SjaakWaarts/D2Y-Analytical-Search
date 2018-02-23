
from datetime import datetime
from django.core.files import File
import glob, os
import pickle
import requests
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
import app.elastic as elastic

categoy_map = {
    4   : 'Competitor News',
    5   : 'Customer News',
    6   : 'General Industry News',
    7   : 'Monthly Highlights'
    }

editor_map = {
    22   : 'Yosef',
    311  : 'Rebecca',
    }

# body is implementd as nested divs
# <div class><div dir><div class>
# next <p> for the section (relevavnce, topline, source, article>
# for each section an <ul> listing the items
# only for article two sub-sections; <div class="itemIntroText"> and <div class="itemFullText"
def scrape_body(mi_post, body):
    bs = BeautifulSoup(body, 'lxml')
    mi_post.relevance = ''
    mi_post.subject = ''
    mi_post.topline = ''
    mi_post.source = ''
    mi_post.article = body
    p_tags = bs.find_all("p")
    for p in p_tags:
        topic = p.get_text()
        list = []
        try:
            ul_tag = p.find_next("ul")
            if ul_tag != None:
                for li_tag in ul_tag.findAll("li"):
                    list.append(li_tag.text)
            if "RELEVANCE:" in topic:
                mi_post.relevance = list
                s = mi_post.relevance[0]
                mi_post.subject = s[:s.find(' - ')+1].strip()
            elif "TOPLINE:" in topic:
                mi_post.topline = list
            elif "SOURCE:" in topic:
                mi_post.source = list
            elif "ARTICLE:" in topic:
                tags = p.find_next_siblings()
                mi_post.article = ''
                for tag in tags:
                    mi_post.article = mi_post.article + tag.get_text()
        except:
            print("scrape body failed for id, title: ", mi_post.post_id, mi_post.title)



def push_posts_to_index():
    id = 1
    data = []
    for index, sp_post in models.posts_df.iterrows():
        mi_post                 = models.PostMap()
        mi_post.post_id         = sp_post.post_id
        if sp_post.editor_id in editor_map:
            mi_post.editor_id   = editor_map[sp_post.editor_id]
        else:
            mi_post.editor_id   = sp_post.editor_id
        mi_post.published_date  = datetime.strptime(sp_post.published_date[0:10],'%Y-%m-%d').date()
        if len(sp_post.post_category_id['results']) > 0:
            post_category_id = sp_post.post_category_id['results'][0]
        else:
            post_category_id = 0
        if post_category_id in categoy_map:
            mi_post.post_category_id = categoy_map[post_category_id]
        else:
            mi_post.post_category_id = post_category_id
        mi_post.title           = sp_post.title.encode("ascii", 'replace')
        #mi_post.relevance, mi_post.subject, mi_post.topline, mi_post.source, mi_post.article = scrape_body(mi_post.title, sp_post.body.encode("ascii", 'replace'))
        scrape_body(mi_post, sp_post.body.encode("ascii", 'replace'))
        try:
            mi_post.average_rating  = float(sp_post.average_rating)
            mi_post.rating_count    = int(sp_post.rating_count)
            mi_post.num_comments_id = int(sp_post.num_comments_id)
        except:
            print("conversion failed", sp_post.average_rating)

        data.append(elastic.convert_for_bulk(mi_post, 'update'))
        id = id + 1

# To add a link the next URL is needed https://iffconnect.iff.com/Fragrances/marketintelligence/Lists/Posts/ViewPost.aspx?ID=2922

    bulk(models.client, actions=data, stats_only=True)


def posts_retrieve(from_year, username, password):
    headers = {'accept': 'application/json;odata=verbose'}
    #user = 'GLOBAL\\sww5648'
    user = username
    pswrd = password
    url =  'https://iffconnect.iff.com/Fragrances/marketintelligence/_api/web/'

    select = "$select=ID,PublishedDate,EditorId,PostCategoryId,Title,Body,AverageRating,RatingCount,NumCommentsId"
    filter = "$filter=(PublishedDate ge datetime'{0}-01-01T00:00:00Z') and (PublishedDate lt datetime'{1}-01-01T00:00:00Z')".format(from_year, from_year+1)   
    top = "$top=3000"
    resp = requests.get(url + "lists/getByTitle('Posts')/items?" + select+"&"+filter+"&"+top, auth=HttpNtlmAuth(user, pswrd), headers=headers)
    if resp.status_code != 200:
        return False
    data = resp.json()
    q = data['d']['results']
    models.posts_df = None
    models.posts_df = DataFrame(q)
    models.posts_df.rename(columns = {
        'ID':'post_id', 'PublishedDate':'published_date',
        'EditorId':'editor_id', 'PostCategoryId':'post_category_id', 'Title':'title',
        'Body':'body', 'AverageRating':'average_rating', 'RatingCount':'rating_count',
        'NumCommentsId':'num_comments_id'
        }, inplace=True)
    models.posts_df.fillna(0, inplace=True)
#    posts_df = posts_df.drop(['co-area', 'profit-ctr','fiscvarnt', 'country', 'prjown', 'plant', 'salesorg', 'ccrsc'], axis=    
    return True

def index_posts(from_date, username, password):
    to_year = datetime.now().year
    from_year = from_date.year
    success = True
    while from_year <= to_year and success:
        print("Market: retieving postings for year %d" % (from_year))
        models.posts_df = None
        success = posts_retrieve(from_year, username, password)
        if success:
            push_posts_to_index()
        from_year = from_year + 1
    return success



