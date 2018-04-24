"""
Definition of models.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.views.generic.base import TemplateView

# Create your models here.
import queue
import collections
import datetime
import FMI.settings
from pandas import DataFrame

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl import DocType, Date, Boolean, Text, Nested, Keyword
from elasticsearch_dsl.connections import connections
import seeker
import app.workbooks as workbooks
import app.wb_excel as wb_excel

from django.utils.encoding import python_2_unicode_compatible


client = Elasticsearch(FMI.settings.ES_HOSTS)


import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'es_index_name', 'es_type_name', 'es_mapping'
)

###
### Excel
###

#
# Based on the headers of an excel file, this ExcelDoc and ExcelSeekerView models are created.
# During Crawl each row of the excel file is turned into a Document and stored in the 'excel' index
# with doc_type the name of the excel file.
# During Search the 'excel' index with the right doc_type is searched.
#

# Class name has to match the name of the mapping in ES (doc_type)
#class ecosystem(models.Model):
#    subset = models.TextField()
#    aop = models.TextField()
#    role = models.TextField()
#    name = models.TextField()
#    url = models.TextField()
#    why = models.TextField()
#    how = models.TextField()
#    what = models.TextField()
#    who = models.TextField()
#    where = models.TextField()
#    country = models.TextField()
#    contacts = models.TextField()
#    company = models.TextField()

#class patents(models.Model):
#    category = models.TextField()
#    publication = models.TextField()
#    title = models.TextField()
#    title_DWPI = models.TextField()
#    url = models.TextField()
#    published_date = models.DateField()
#    assignee = models.TextField()
#    assignee_DWPI = models.TextField()
#    abstract = models.TextField()

#class ingr_molecules(models.Model):
#    IPC = models.TextField()
#    name = models.TextField()
#    year = models.TextField()
#    nr_of_IPCs = models.IntegerField()
#    nr_of_IPCs_SC = models.IntegerField()
#    selling_IPCs = models.IntegerField()
#    FITTE_score = models.FloatField()
#    FITTE_norm = models.FloatField()
#    regions = models.IntegerField()
#    flavor_classes = models.TextField()
#    sales_val = models.FloatField()
#    sales_vol = models.FloatField()
#    tech_vol = models.FloatField()
#    bucket = models.TextField()
#    cost = models.FloatField()
#    use_level = models.TextField()
#    low_medium_high = models.FloatField()
#    CIU = models.FloatField()
#    regulator = models.TextField()


class ExcelSeekerView (seeker.SeekerView):
    document = None
    using = client
    index = "excel"
    page_size = 30
    facets = [
        ]
    facets_keyword = [];
    display = [
        ]
    sort = []
    summary = []
    sumheader = []
    SUMMARY_URL="{}"
    urlfields = {
        }
    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

###
### Fragrantica
###

# Class name has to match the name of the mapping in ES (doc_type)
class Perfume(models.Model):
    site = models.TextField()
    brand_name = models.TextField()
    brand_variant = models.TextField()
    perfume = models.TextField()
    review_date = models.DateField()
    review = models.TextField()
    label = models.TextField()
    accords = models.TextField()
    notespyramid = models.TextField()
    moods = models.TextField()
    notes = models.TextField()
    longevity = models.TextField()
    sillage = models.TextField()
    ratings = models.TextField()
    img_src = models.TextField()

class Review(models.Model):
    reviewid = models.IntegerField()
    site = models.TextField()
    brand_name = models.TextField()
    brand_variant = models.TextField()
    perfume = models.TextField()
    review_date = models.DateField()
    review = models.TextField()
    label = models.TextField()
    accords = []
    notespyramid = {}
    moods = []
    notes = []
    longevity = []
    sillage = []
    ratings = []
    img_src = models.TextField()

    class Meta:
        es_index_name = 'review'
        es_type_name = 'perfume'
        es_mapping = {
            'properties' : {
                'site'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'brand'          : {
                    'properties' : {
                        'name'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'variant'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'perfume'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'review_date'   : {'type' : 'date'},
                'review'        : {'type' : 'text'},
                'label'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'accords'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'notespyramid' :  {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'moods'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'notes'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'longevity'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'sillage'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'ratings'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'val'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc'   : {'type' : 'float'},
                        }
                    },
                'img_src'        : {'type' : 'text'},
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.reviewid
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_brand(self):
        return {'name': self.brand_name, 'variant': self.brand_variant}
    def get_es_accords(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.accords.items()]
    def get_es_moods(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.moods.items()]
    def get_es_notes(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.notes.items()]
    def get_es_longevity(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.longevity.items()]
    def get_es_sillage(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.sillage.items()]
    def get_es_ratings(self):
        return [{'val': accord, 'prc': votes} for accord, votes in self.ratings.items()]


class PerfumeSeekerView (seeker.SeekerView):
    document = None
    using = client
    index = "review"
    page_size = 30
    facets = [
        seeker.TermsFacet("site.keyword", label = "Site"),
        seeker.TermsFacet("brand.name.keyword", label = "Brand"),
        seeker.TermsFacet("perfume.keyword", label = "Perfume"),
        #seeker.YearHistogram("review_date", label = "Reviewed"),
        seeker.MonthHistogram("review_date", label = "Reviewed"),
        seeker.TermsFacet("label.keyword", label = "Sentiment"),
        seeker.TermsFacet("notespyramid.keyword", label = "Top Notes Pyramid"),
        seeker.NestedFacet("accords.val.keyword", label = "Accords", nestedfield="accords"),
        seeker.NestedFacet("moods.val.keyword", label = "Moods", nestedfield="moods"),
        seeker.NestedFacet("notes.val.keyword", label = "Notes", nestedfield="notes"),
        seeker.NestedFacet("longevity.val.keyword", label = "Longevity", nestedfield="longevity", visible_pos=0),
        seeker.NestedFacet("sillage.val.keyword", label = "Sillage", nestedfield="sillage", visible_pos=0),
        seeker.NestedFacet("ratings.val.keyword", label = "Ratings", nestedfield="ratings", visible_pos=0),
        ]
    facets_keyword = [seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k")];
    display = [
        "perfume",
        "review_date",
        "img_src",
        "site",
        "review",
        "label",
        "accords"
        ]
    field_labels = {
        "notespyramid" : "Top Notes",
        }
    sort = [
        "-review_date"
        ]
    summary = ['review']
    sumheader = ['perfume']
    SUMMARY_URL="{}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    dashboard = {
        'perfume_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Perfume / Keyword Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "perfume.keyword",
                'label'   : "Perfume" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_label_table" : {
            'chart_type': "Table",
            'chart_title' : "Keyword / Category Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'Y_facet'     : {
                'field'   : "label.keyword",
                'label'   : "Label" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "reviewed_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Reviewed Year-Month Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "review_date",
                'label'   : "Reviewed",
                'key'     : 'key_as_string'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "cand_moods_like_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Moods-Like Perfumes",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'help'        : "Select Row for sorting, Select Column Header for filter",
            'listener'    : {'select' : {'colsort': None, 'rowcolfilter': ["accords_cand_radar", "moods_cand_radar", "notes_cand_radar",
                                                                           "longevity_cand_radar", "sillage_cand_radar", "ratings_cand_radar"]}},
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "moods",
                'question': "moods",
                "answers" : ['like'], # All
                "metric"  : "prc",
                #"a-mean"  : True,
                'label'   : "Moods-Like",
                }
            },
        "accords_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Accords",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "accords",
                'question': "accords",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Accords"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "moods_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Moods",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "moods",
                'question': "moods",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Moods"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "notes_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Notes",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "notes",
                'question': "notes",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Notes"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "longevity_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Longevity",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "longevity",
                'question': "longevity",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Longevity"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "sillage_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Sillage",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "sillage",
                'question': "sillage",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Sillage"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        "ratings_cand_radar" : {
            'chart_type'  : "RadarChart",
            'chart_title' : "Ratings",
            'data_type'  : "hits",
            'controls'    : ['CategoryFilter'],
            'transpose'   : True,
            'X_facet'     : {
                'field'   : "perfume",
                'label'   : "Perfume",
                'total'   : False
                },
            'Y_facet'     : {
                'field'   : "ratings",
                'question': "ratings",
                "answers" : [], # All
                "metric"  : "prc",
                "a-mean"  : True,
                'label'   : "Ratings"
                },
            'options'     : {
                'width'   : 300,
                'height'  : 300
                },
            },
        }

    dashboard_layout = collections.OrderedDict()
    dashboard_layout['table1'] = [["reviewed_keyword_line"], ["keyword_label_table"]]
    dashboard_layout['table2'] = [["perfume_keyword_table", "keyword_pie"]]

    dashboard_profile = collections.OrderedDict()
    dashboard_profile['table1'] = [["cand_moods_like_col"],
                                   ["accords_cand_radar", "moods_cand_radar"],
                                   ["longevity_cand_radar", "sillage_cand_radar"],
                                   ["notes_cand_radar", "ratings_cand_radar"],
                                   ]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         },
        {'name' : 'profile',
         'layout'   : dashboard_profile,
         }
    ]


###
### Market Intelligence
###

class Post(models.Model):
    editor_id = models.CharField(max_length=30)
    published_date = models.DateField()
    post_category_id = models.CharField(max_length=30)
    title = models.CharField(max_length=256)
    relevance = models.TextField()
    subject = models.TextField()
    topline = models.TextField()
    source = models.TextField()
    article = models.TextField()
    average_rating = models.FloatField()
    rating_count = models.IntegerField()
    num_comments_id = models.IntegerField()

#class PostDoc(seeker.ModelIndex):
# done by models.PostDoc = seeker.mapping.document_from_model(models.Post, index="post", using=models.client)
class PostMap(models.Model):
    post_id = models.IntegerField()
    editor_id = models.CharField(max_length=30)
    published_date = models.DateField()
    post_category_id = models.CharField(max_length=30)
    title = models.CharField(max_length=256)
    relevance = models.TextField()
    subject = models.TextField()
    topline = models.TextField()
    source = models.TextField()
    article = models.TextField()
    average_rating = models.FloatField()
    rating_count = models.IntegerField()
    num_comments_id = models.IntegerField()
    class Meta:
        es_index_name = 'post'
        es_type_name = 'post'
        es_mapping = {
            'properties' : {
                'editor_id'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'published_date'    : {'type' : 'date'},
                'post_category_id'  : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'             : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'relevance'         : {'type' : 'text'},
                'subject'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'topline'           : {'type' : 'text'},
                'source'            : {'type' : 'text'},
                'article'           : {'type' : 'text'},
                'average_rating'    : {'type' : 'float'},
                'rating_count'      : {'type' : 'integer', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'num_comments_id'   : {'type' : 'integer', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_article(self, field_name):
        list_es_value = getattr(self, field_name)
        if len(list_es_value) > 32766:
            list_es_value = list_es_value[:32766]
        return list_es_value


class PostSeekerView (seeker.SeekerView, workbooks.PostWorkbook):
    document = None
    using = client
    index = "post"
    page_size = 30
    facets = [
        seeker.TermsFacet("post_category_id.keyword", label = "Category"),
        seeker.TermsFacet("editor_id.keyword", label = "Editor"),
        seeker.TermsFacet("subject.keyword", label = "Subject"),
        #seeker.YearHistogram("published_date", label = "Published Year"),
        seeker.MonthHistogram("published_date", label = "Published Month"),
        #seeker.RangeFilter("rating_count", label = "Rating"),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "post_category_id",
        "published_date",
        "title",
        "subject",
        "relevance",
        "topline"
        ]
    summary = [
        "article"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="https://iffconnect.iff.com/Fragrances/marketintelligence/Lists/Posts/ViewPost.aspx?ID={}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}


###
### Costmetics
###

class Page(models.Model):
    page_id = models.IntegerField()
    published_date = models.DateField()
    site = models.TextField()
    sub_site = models.TextField()
    section = models.TextField()
    title = models.TextField()
    url = models.TextField()
    img_src = models.TextField()
    page = models.TextField()

class PageMap(models.Model):
    page_id = models.IntegerField()
    published_date = models.DateField()
    site = models.TextField()
    sub_site = models.TextField()
    section = models.TextField()
    title = models.TextField()
    url = models.TextField()
    img_src = models.TextField()
    page = models.TextField()

    class Meta:
        es_index_name = 'page'
        es_type_name = 'page'
        es_mapping = {
            'properties' : {
                'published_date': {'type' : 'date'},
                'site'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'sub_site'      : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'section'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'         : {'type' : 'text'},
                'url'           : {'type' : 'text'},
                'img_src'       : {'type' : 'text'},
                'page'          : {'type' : 'text'},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.page_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value


class PageSeekerView (seeker.SeekerView, workbooks.PageWorkbook):
    document = None
    using = client
    index = "page"
    page_size = 30
    facets = [
        seeker.TermsFacet("site.keyword", label = "Site"),
        seeker.TermsFacet("sub_site.keyword", label = "Sub Site"),
        seeker.TermsFacet("section.keyword", label = "Section"),
        seeker.MonthHistogram("published_date", label = "Published Month"),
        seeker.YearHistogram("published_date", label = "Published Year")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "published_date",
        "title",
        "site",
        "sub_site",
        ]
    summary = [
        "page"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="{}"


    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = collections.OrderedDict()
    dashboard_layout = {}
    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ] 

###
### FEEDLY
###

class Feedly(models.Model):
    post_id = models.IntegerField()
    subset = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    feed = models.TextField()
    feed_topics = models.TextField()
    body_topics = models.TextField()
    title = models.TextField()
    url = models.TextField()
    body = models.TextField()
 
class FeedlyMap(models.Model):
    post_id = models.IntegerField()
    subset = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    feed = models.TextField()
    feed_topics = models.TextField()
    body_topics = models.TextField()
    title = models.TextField()
    url = models.TextField()
    body = models.TextField()

    class Meta:
        es_index_name = 'feedly'
        es_type_name = 'feedly'
        es_mapping = {
            'properties' : {
                'published_date'    : {'type' : 'date'},
                'subset'            : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'category'          : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'feed'              : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'feed_topics'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'body_topics'       : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'title'             : {'type' : 'text'},
                'url'               : {'type' : 'text'},
                'body'              : {'type' : 'text'},
                #'body'              : {'type' : 'text', 'fields' : {
                #    'body_keepwords'    : {'type': 'text', 'analyzer': 'keepwords'},
                #    'body_keeplength'   : {'type': 'token_count', 'analyzer': 'keepwords'}}},
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value


class FeedlySeekerView (seeker.SeekerView):
    document = None
    using = client
    index = "feedly"
    page_size = 30
    facets = [
        seeker.TermsFacet("subset.keyword", label = "Subset"),
        seeker.TermsFacet("category.keyword", label = "Category"),
        seeker.TermsFacet("feed.keyword", label = "Feed"),
        seeker.TermsFacet("feed_topics.keyword", label = "Topics"),
        seeker.DayHistogram("published_date", label = "Published")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        seeker.KeywordFacet("facet_cust", label = "Customers", input="keywords_cust",
                            initial="unilever, procter & gamble, P&G, sc johnson, johnson & johnson, henkel"),
        seeker.KeywordFacet("facet_comp", label = "Competitors", input="keywords_comp",
                            initial="symrise, givaudan, firmenich, frutarom")
        ];
    display = [
        "published_date",
        "title",
        "category",
        "feed",
        "feed_topics",
        "body_topics",
        ]
    summary = [
        "body"
        ]
    sumheader = [
        "title"
        ]
    urlfields = {
        "title" : ""
        }
    SUMMARY_URL="{}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = {
        'category_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Category / Keyword Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "category.keyword",
                'label'   : "Category" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        'feed_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "Feed / Keyword Count",
            'data_type'  : "aggr",
            'X_facet'     : {
                'field'   : "feed.keyword",
                'label'   : "Feed" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "customer_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Customer Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_cust",
                'label'   : "Customer" },
            },
        "competitor_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Competitor Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_comp",
                'label'   : "Competitor" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Year Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'key'     : 'key_as_string',
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM/d'},
                },
            },
        }
    dashboard_layout = collections.OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"], ["customer_pie", "competitor_pie", "keyword_pie"]]
    dashboard_layout['rows2'] = [["category_keyword_table", "feed_keyword_table"]]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ]       

###
### MAIL
###

class Mail(models.Model):
    post_id = models.IntegerField()
    to_addr = models.TextField()
    from_addr = models.TextField()
    published_date = models.DateField()
    subject = models.TextField()
    links = models.TextField()
    url = models.TextField()
    body = models.TextField()

class MailMap(models.Model):
    post_id = models.IntegerField()
    to_addr = models.TextField()
    from_addr = models.TextField()
    published_date = models.DateField()
    subject = models.TextField()
    links = models.TextField()
    url = models.TextField()
    body = models.TextField()

    class Meta:
        es_index_name = 'mail'
        es_type_name = 'mail'
        es_mapping = {
            'properties' : {
                'to_addr'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'from_addr'         : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'published_date'    : {'type' : 'date'},
                'subject'           : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                'body'              : {'type' : 'text'},
                'links'             : {
                                        'type'       : 'nested',
                                        'properties' : {
                                            'name' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                            'url'  : {'type' : 'text', 'index': 'false'},
                                            'body' : {'type' : 'text'},
                                            }
                    },
                }
            }
    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.post_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value
    def get_es_links(self, field_name):
        return [{'name': link[0], 'url': link[1], 'body': link[2]} for link in self.links]


class MailSeekerView (seeker.SeekerView):
    document = None
    using = client
    index = "mail"
    page_size = 30
    field_column_types = {'links': 'LinksColumn'}
    facets = [
        seeker.TermsFacet("to_addr.keyword", label = "To"),
        seeker.TermsFacet("from_addr.keyword", label = "From"),
        seeker.TermsFacet("subject.keyword", label = "Subject"),
        seeker.DayHistogram("published_date", label = "Published")
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Keywords", input="keywords_k"),
        ];
    display = [
        "published_date",
        "from_addr",
        "subject",
        ]
    search_children = ['links.body']
    summary = [
        "body"
        ]
    sumheader = [
        "subject"
        ]
    urlfields = {
        "subject" : ""
        }
    SUMMARY_URL="{}"

    tabs = {'results_tab': 'active', 'summary_tab': '', 'storyboard_tab': '', 'insights_tab': 'hide'}

    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements
    dashboard = {
        'from_keyword_table' : {
            'chart_type'  : "Table",
            'chart_title' : "From / Keyword Doc Count",
            'data_type'  : "aggr",
            'controls'    : ['CategoryFilter'],
            'X_facet'     : {
                'field'   : "from_addr.keyword",
                'label'   : "From" },
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "keyword_pie" : {
            'chart_type': "PieChart",
            'chart_title' : "Keyword Doc Count",
            'data_type'  : "facet",
            'X_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            },
        "published_keyword_line" : {
            'chart_type'  : "LineChart",
            'chart_title' : "Published Year Doc Count",
            'data_type'  : "aggr",
            'controls'    : ['ChartRangeFilter'],
            'X_facet'     : {
                'field'   : "published_date",
                'label'   : "Published",
                'key'     : 'key_as_string',
                'total'   : False,
                'type'    : 'date'},
            'Y_facet'     : {
                'field'   : "facet_keyword",
                'label'   : "Keywords" },
            'options'     : {
                "hAxis"   : {'format': 'yy/MMM/d'},
                },
            },
        }
    dashboard_layout = collections.OrderedDict()
    dashboard_layout['rows1'] = [["published_keyword_line"], ["from_keyword_table", "keyword_pie"]]

    storyboard = [
        {'name' : 'initial',
         'layout'   : dashboard_layout,
         #'active'   : True,
         }
    ]       


###
### Scent Emotion (CFT - Ingredients)
###

class Scentemotion(models.Model):
    cft_id = models.IntegerField()
    dataset = models.TextField()
    ingr_name = models.TextField()
    IPC = models.TextField()
    supplier = models.TextField()
    olfactive = models.TextField()
    region = models.TextField()
    review = models.TextField()
    dilution = models.TextField()
    intensity = models.TextField()
    mood = models.TextField()
    smell = models.TextField()
    negative = models.TextField()
    descriptor = models.TextField()
    color = models.TextField()
    texture = models.TextField()
    emotion = models.TextField()
    hedonics = models.TextField()

 
class ScentemotionMap(models.Model):
    cft_id = models.IntegerField()
    dataset = models.TextField()
    ingr_name = models.TextField()
    IPC = models.TextField()
    supplier = models.TextField()
    olfactive = models.TextField()
    region = models.TextField()
    review = models.TextField()
    dilution = models.TextField()
    intensity = models.TextField()
    mood = []
    smell = []
    negative = []
    descriptor = []
    color = []
    texture = []
    emotion = []
    hedonics = []

    class Meta:
        es_index_name = 'scentemotion'
        es_type_name = 'scentemotion'
        es_mapping = {
            "properties" : {
                "dataset"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "ingr_name"         : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                "IPC"               : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "supplier"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "olfactive"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "region"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "review"            : {"type" : "text"},
                "dilution"          : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                "intensity"         : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                'mood'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'smell'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'negative'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'descriptor'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'color'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'texture'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'emotion'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'hedonics'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.cft_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def get_es_mood(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_smell(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_negative(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_descriptor(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_color(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_texture(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_emotion(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_hedonics(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
                if config['type'] == 'integer' and type(field_es_value) == str:
                    field_es_value = int(float(field_es_value))
                if (config['type'] == 'string' or config['type'] == 'text') and type(field_es_value) == int:
                    field_es_value = "{0:d}".format(field_es_value)
        return field_es_value


class ScentemotionSeekerView (seeker.SeekerView, workbooks.ScentemotionWorkbook):
    document = None
    using = client
    index = "scentemotion"
    page_size = 20
    facets = [
        seeker.TermsFacet("dataset.keyword", label = "Dataset / Survey"),
        seeker.TermsFacet("olfactive.keyword", label = "Olfactive"),
        seeker.TermsFacet("region.keyword", label = "Region"),
        seeker.TermsFacet("IPC.keyword", label = "IPC", visible_pos=0),
        seeker.TermsFacet("intensity", label = "Intensity", nestedfield="intensity", visible_pos=0),
        #seeker.TermsFacet("mood.keyword", label = "Mood"),
        #seeker.TermsFacet("smell.keyword", label = "Smell"),
        seeker.NestedFacet("mood.val.keyword", label = "Mood", nestedfield="mood"),
        seeker.NestedFacet("smell.val.keyword", label = "Smell", nestedfield="smell"),
        seeker.NestedFacet("negative.val.keyword", label = "Negative", nestedfield="negative"),
        seeker.NestedFacet("descriptor.val.keyword", label = "Descriptor", nestedfield="descriptor"),
        seeker.NestedFacet("color.val.keyword", label = "Color", nestedfield="color"),
        seeker.NestedFacet("texture.val.keyword", label = "Texture", nestedfield="texture"),
        seeker.NestedFacet("emotion.val.keyword", label = "Emotion", nestedfield="emotion", visible_pos=0),
        seeker.NestedFacet("hedonics.val.keyword", label = "Hedonics", nestedfield="hedonics", visible_pos=0),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Benchmark", input="keywords_k"),
        ];
    display = [
        "IPC",
        "ingr_name",
        "olfactive",
        'intensity',
        "descriptor",
        "region",
        "mood",
        "smell",
        "negative",
        "review",
        ]
    sort = [
        #"-descriptor"
    ]
    exclude = [
        "cft_id",
        "dataset",  
        ]
    field_labels = {
        "mood"        : "Mood",
        "smell"       : "Smell",
        "negative"    : "Negative",
        "descriptor"  : "Descr",
        "color"       : "Color",
        "texture"     : "Texture"
        }
    summary = [
        ]
    sumheader = ["ingr_name"]
    urlfields = {
        "IPC"       : "http://sappw1.iff.com:50200/irj/servlet/prt/portal/prtroot/com.sap.ip.bi.designstudio.nw.portal.ds?APPLICATION=E2ESCENARIO_002?{0}",
        "ingr_name" : "http://www.iff.com/smell/online-compendium#{0}"
        }
    SUMMARY_URL="http://www.iff.com/smell/online-compendium#amber-xtreme"

    tabs = {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'}
      
    # A dashboard layout is a dictionary of tables. Each table is a list of rows and each row is a list of charts
    # in the template this is translated into HTML tables, rows, cells and div elements


###
### Scent Emotion (CFT - CI Studies)
###

class Studies(models.Model):
    cft_id = models.IntegerField()
    survey = models.TextField()
    blindcode = models.TextField()
    fragr_name = models.TextField()
    IPC = models.TextField()
    CRP = models.TextField()
    olfactive = models.TextField()
    region = models.TextField()
    intensity = models.TextField()
    perception = models.TextField()
    method = models.TextField()
    product_form = models.TextField()
    freshness = models.IntegerField()
    cleanliness = models.IntegerField()
    lastingness  = models.IntegerField()
    intensity = models.IntegerField()
    liking = models.TextField()
    concept = models.TextField()
    emotion = models.TextField()
    fragrattr = models.TextField()
    mood = models.TextField()
    smell = models.TextField()
    suitable_product = models.TextField()
    suitable_stage = models.TextField()
    hedonics = models.TextField()

 
class StudiesMap(models.Model):
    cft_id = models.IntegerField()
    survey = models.TextField()
    blindcode = models.TextField()
    fragr_name = models.TextField()
    IPC = models.TextField()
    CRP = models.TextField()
    olfactive = models.TextField()
    region = models.TextField()
    intensity = models.TextField()
    perception = []
    method = []
    product_form = []
    freshness = []
    cleanliness = []
    lastingness  = []
    intensity = []
    liking = []
    concept = []
    emotion = []
    fragrattr = []
    mood = []
    smell = []
    suitable_product = []
    suitable_stage = []
    hedonics = []

    class Meta:
        es_index_name = 'studies'
        es_type_name = 'studies'
        es_mapping = {
            "properties" : {
                "survey"            : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "blindcode"         : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "fragr_name"        : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                "IPC"               : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "CRP"               : {"type" : "text"},
                "olfactive"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "region"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "intensity"         : {"type" : "text", "fields" : {"raw" : {"type" : "text", "index" : "false"}}},
                'perception'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'method'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'product_form'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'freshness'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'cleanliness'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'lastingness'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'intensity'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'liking'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },

                'concept'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'emotion'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'fragrattr'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'mood'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'smell'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'suitable_product'         : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'suitable_stage'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                'hedonics'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'val' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'prc' : {'type' : 'float'},
                        }
                    },
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.cft_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def get_es_perception(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_method(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_product_form(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_freshness(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_cleanliness(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_lastingness(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_intensity(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_liking(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_concept(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_emotion(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_fragrattr(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_mood(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_smell(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_suitable_product(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_suitable_stage(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def get_es_hedonics(self, field_name):
        list_es_value = getattr(self, field_name)
        field_es_value = [{'val':t[0], 'prc':t[1]} for t in list_es_value]
        return field_es_value
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
                if config['type'] == 'integer' and type(field_es_value) == str:
                    field_es_value = int(float(field_es_value))
                if (config['type'] == 'string' or config['type'] == 'text') and type(field_es_value) == int:
                    field_es_value = "{0:d}".format(field_es_value)
        return field_es_value


class StudiesSeekerView (seeker.SeekerView, workbooks.StudiesWorkbook):
    document = None
    using = client
    index = "studies"
    page_size = 20
    facets = [
        seeker.TermsFacet("survey.keyword", label = "Survey"),
        seeker.TermsFacet("blindcode.keyword", label = "Blind Code", visible_pos=1),
        seeker.TermsFacet("olfactive.keyword", label = "Olfactive"),
        seeker.TermsFacet("region.keyword", label = "Region", visible_pos=0),
        seeker.TermsFacet("IPC.keyword", label = "IPC", visible_pos=1),
        seeker.NestedFacet("perception.val.keyword", label = "Perception", nestedfield="perception", visible_pos=0),
        seeker.NestedFacet("method.val.keyword", label = "Method", nestedfield="method", visible_pos=1),
        seeker.NestedFacet("product_form.val.keyword", label = "Product Form", nestedfield="product_form", visible_pos=0),
        seeker.NestedFacet("freshness.val.keyword", label = "Freshness", nestedfield="freshness", visible_pos=1),
        seeker.NestedFacet("cleanliness.val.keyword", label = "Cleanliness", nestedfield="cleanliness", visible_pos=0),
        seeker.NestedFacet("lastingness.val.keyword", label = "Lastingness", nestedfield="lastingness", visible_pos=0),
        seeker.NestedFacet("intensity.val.keyword", label = "Intensity", nestedfield="intensity", visible_pos=0),
        seeker.NestedFacet("liking.val.keyword", label = "Liking", nestedfield="liking", visible_pos=0),
        seeker.NestedFacet("concept.val.keyword", label = "Concept", nestedfield="concept", visible_pos=0),
        seeker.NestedFacet("emotion.val.keyword", label = "Emotion", nestedfield="emotion", visible_pos=1),
        seeker.NestedFacet("fragrattr.val.keyword", label = "Fragr Attr", nestedfield="fragrattr", visible_pos=0),
        seeker.NestedFacet("mood.val.keyword", label = "Mood", nestedfield="mood", visible_pos=0),
        seeker.NestedFacet("smell.val.keyword", label = "Smell", nestedfield="smell", visible_pos=0),
        seeker.NestedFacet("suitable_product.val.keyword", label = "Suitable Product", nestedfield="suitable_product", visible_pos=0),
        seeker.NestedFacet("suitable_stage.val.keyword", label = "Suitable Stage", nestedfield="suitable_stage", visible_pos=1),
        seeker.NestedFacet("hedonics.val.keyword", label = "Hedonics", nestedfield="hedonics", visible_pos=1),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Benchmark", input="keywords_k"),
        ];
    display = [
        "blindcode",
        "IPC",
        "CRP",
        "olfactive",
        "emotion",
        "hedonics",
        ]
    sort = [
        "-hedonics"
    ]
    exclude = [
        "cft_id",
        "survey",  
        ]
    field_labels = {
        "mood"        : "Mood",
        "smell"       : "Smell",
        "negative"    : "Negative",
        "descriptor"  : "Descr",
        "color"       : "Color",
        "texture"     : "Texture"
        }
    summary = [
        ]
    sumheader = ["fragr_name"]
    urlfields = {
        "IPC"       : "http://sappw1.iff.com:50200/irj/servlet/prt/portal/prtroot/com.sap.ip.bi.designstudio.nw.portal.ds?APPLICATION=E2ESCENARIO_002?{0}",
        "blindcode" : "http://10.20.33.102/FMI/guide?site_select=panels&menu_name=CRP&view_name=project-mona-lisa&workbook_name=&storyboard_name=&dashboard_name=&benchmark=&tile_facet_field=&tile_facet_value="
        }
    SUMMARY_URL="http://www.iff.com/smell/online-compendium#amber-xtreme"

    tabs = {'results_tab': 'active', 'summary_tab': 'hide', 'storyboard_tab': '', 'insights_tab': 'hide'}

###
### Survey (CI)
###

class Survey(models.Model):
    # Survey attributes
    survey = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    stage = models.TextField()
    # Respondent Attributes
    resp_id = models.TextField()
    group_id = models.TextField()
    country = models.TextField()
    gender = models.TextField()
    age = models.TextField()
    ethnics = models.TextField()
    city = models.TextField()
    regions = models.TextField()
    education = models.TextField()
    income = models.TextField()
    # Product attributes
    blindcode = models.TextField()
    cluster = models.TextField()
    brand = models.TextField()
    variant = models.TextField()
    # Questions
    olfactive = models.TextField()
    method = models.TextField()
    product_form = models.TextField()
    # Ordinal Questions
    perception = models.TextField()
    freshness = models.IntegerField()
    cleanliness = models.IntegerField()
    lastingness  = models.IntegerField()
    intensity = models.IntegerField()
    liking = models.TextField()
    # Binary Questions
    affective = models.TextField()
    ballot = models.TextField()
    behavioral = models.TextField()
    children = models.TextField()
    concept = models.TextField()
    descriptors = models.TextField()
    descriptors1 = models.TextField()
    descriptors2 = models.TextField()
    descriptors3 = models.TextField()
    descriptors4 = models.TextField()
    emotion = models.TextField()
    fragrattr = models.TextField()
    hedonics = models.TextField()
    imagine = models.TextField()
    mood = models.TextField()
    physical = models.TextField()
    smell = models.TextField()
    suitable_product = models.TextField()
    suitable_stage = models.TextField()
    # Fit Questions
    fit_descriptors1 = models.TextField()
    fit_descriptors2 = models.TextField()
    fit_descriptors3 = models.TextField()
    fit_descriptors4 = models.TextField()

class SurveyMap(models.Model):
    # Survey attributes
    survey = models.TextField()
    published_date = models.DateField()
    category = models.TextField()
    stage = models.TextField()
    # Respondent Attributes
    resp_id = models.TextField()
    group_id = models.TextField()
    country = models.TextField()
    gender = models.TextField()
    age = models.TextField()
    ethnics = models.TextField()
    city = models.TextField()
    regions = models.TextField()
    education = models.TextField()
    income = models.TextField()
    # Product attributes
    blindcode = models.TextField()
    cluster = models.TextField()
    brand = models.TextField()
    variant = models.TextField()
    # Questions
    olfactive = models.TextField()
    method = models.TextField()
    product_form = models.TextField()
    # Ordinal Questions
    perception = models.TextField()
    freshness = models.IntegerField()
    cleanliness = models.IntegerField()
    lastingness  = models.IntegerField()
    intensity = models.IntegerField()
    liking = models.TextField()
    # Binary Questions
    affective = []
    ballot = []
    behavioral = []
    children = []
    concept = []
    descriptors = []
    descriptors1 = []
    descriptors2 = []
    descriptors3 = []
    descriptors4 = []
    emotion = []
    fragrattr = []
    hedonics = []
    imagine = []
    mood = []
    physical = []
    smell = []
    suitable_product = []
    suitable_stage = []
    # Fit Questions
    fit_descriptors1 = []
    fit_descriptors2 = []
    fit_descriptors3 = []
    fit_descriptors4 = []

    class Meta:
        es_index_name = 'survey'
        es_type_name = 'survey'
        es_mapping = {
            "properties" : {
                "survey"            : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                'published_date'    : {'type' : 'date'},
                #"category"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                'category'          : {
                    'properties' : {
                        'cat' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'subcat'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                "stage"             : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "resp_id"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "group_id"          : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "country"           : {"type" : "text", "fields" : {"keyword" : {"type" : "keyword", "ignore_above" : 256}}},
                "cluster"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "gender"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "age"               : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "ethnics"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "city"              : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "regions"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "education"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "income"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "blindcode"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "brand"             : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "variant"           : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "olfactive"         : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "perception"        : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "method"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                "product_form"      : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},
                'freshness'         : {'type' : 'integer'},
                'cleanliness'       : {'type' : 'integer'},
                'lastingness'       : {'type' : 'integer'},
                'intensity'         : {'type' : 'integer'},
                "liking"            : {"type" : "text", "fields" : {
                                            "keyword" : {"type" : "keyword", "ignore_above" : 256},
                                            "raw" : {"type" : "text", "index" : "false"}
                                       }},

                'affective'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'ballot'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'behavioral'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'children'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'concept'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors1'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors2'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors3'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'descriptors4'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'emotion'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fragrattr'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'hedonics'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'imagine'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'mood'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'physical'              : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'smell'          : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'suitable_product'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'suitable_stage'       : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors1'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors2'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors3'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                'fit_descriptors4'      : {
                    'type'       : 'nested',
                    'properties' : {
                        'question' : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        'answer'   : {'type' : 'text', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                        }
                    },
                }
            }

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.resp_id
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data
    def field_es_repr(self, field_name):
        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)(field_name)
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
                if config['type'] == 'integer' and type(field_es_value) == str:
                    field_es_value = int(float(field_es_value))
        return field_es_value
    def get_es_affective(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.affective.items()]
    def get_es_ballot(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.ballot.items()]
    def get_es_behavioral(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.behavioral.items()]
    def get_es_children(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.children.items()]
    def get_es_concept(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.concept.items()]
    def get_es_descriptors(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors.items()]
    def get_es_descriptors1(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors1.items()]
    def get_es_descriptors2(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors2.items()]
    def get_es_descriptors3(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors3.items()]
    def get_es_descriptors4(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.descriptors4.items()]
    def get_es_emotion(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.emotion.items()]
    def get_es_fragrattr(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fragrattr.items()]
    def get_es_hedonics(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.hedonics.items()]
    def get_es_imagine(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.imagine.items()]
    def get_es_mood(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.mood.items()]
    def get_es_physical(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.physical.items()]
    def get_es_smell(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.smell.items()]
    def get_es_suitable_product(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.suitable_product.items()]
    def get_es_suitable_stage(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.suitable_stage.items()]
    def get_es_fit_descriptors1(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors1.items()]
    def get_es_fit_descriptors2(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors2.items()]
    def get_es_fit_descriptors3(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors3.items()]
    def get_es_fit_descriptors4(self, field_name):
        return [{'question': q, 'answer': a} for q, a in self.fit_descriptors4.items()]


class SurveySeekerView (seeker.SeekerView, workbooks.SurveyWorkbook):
    document = None
    using = client
    index = "survey"
    page_size = 30
    facets = [
        seeker.TermsFacet("survey.keyword", label = "Survey"),
        seeker.YearHistogram("published_date", label = "Published"),
        seeker.TermsFacet("group_id.keyword", label = "Group"),
        seeker.TermsFacet("category.cat.keyword", label = "Category"),
        seeker.TermsFacet("category.subcat.keyword", label = "Sub-Category"),
        seeker.TermsFacet("stage.keyword", label = "Stage"),
        seeker.TermsFacet("country.keyword", label = "Country"),
        seeker.TermsFacet("regions.keyword", label = "Region", visible_pos=0),
        seeker.TermsFacet("city.keyword", label = "City", visible_pos=0),
        seeker.TermsFacet("gender.keyword", label = "Gender"),
        seeker.TermsFacet("ethnics.keyword", label = "Ethnics", visible_pos=0),
        seeker.TermsFacet("income.keyword", label = "Income", visible_pos=0),
        seeker.TermsFacet("age.keyword", label = "Age"),
        #seeker.RangeFilter("age", label = "Age"),
        seeker.TermsFacet("cluster.keyword", label = "Cluster"),
        seeker.TermsFacet("brand.keyword", label = "Brand"),
        seeker.TermsFacet("product_form.keyword", label = "Product Form"),
        seeker.TermsFacet("method.keyword", label = "Method"),
        seeker.TermsFacet("blindcode.keyword", label = "Blind Code"),
        seeker.TermsFacet("olfactive.keyword", label = "Olfactive"),
        seeker.TermsFacet("perception.keyword", label = "Perception"),
        seeker.TermsFacet("liking.keyword", label = "Liking/Hedonics", order={"_key":"desc"}),
        seeker.TermsFacet("freshness", label = "Freshness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("cleanliness", label = "Cleanliness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("lastingness", label = "Lastingness", visible_pos=0, order={"_key":"desc"}),
        seeker.TermsFacet("intensity", label = "Intensity", visible_pos=0, order={"_key":"desc"}),
        seeker.OptionFacet("affective", label = "Affective", nestedfield="affective", visible_pos=0),
        seeker.OptionFacet("ballot", label = "Ballot", nestedfield="ballot", visible_pos=0),
        seeker.OptionFacet("behavioral", label = "Behavioral", nestedfield="behavioral", visible_pos=0),
        seeker.OptionFacet("children", label = "Children", nestedfield="children", visible_pos=0),
        seeker.OptionFacet("concept", label = "Concept", nestedfield="concept", visible_pos=0),
        seeker.OptionFacet("descriptors", label = "Descriptors", nestedfield="descriptors", visible_pos=0),
        seeker.OptionFacet("descriptors1", label = "Descriptors1", nestedfield="descriptors1", visible_pos=0),
        seeker.OptionFacet("descriptors2", label = "Descriptors2", nestedfield="descriptors2", visible_pos=0),
        seeker.OptionFacet("descriptors3", label = "Descriptors3", nestedfield="descriptors3", visible_pos=0),
        seeker.OptionFacet("descriptors4", label = "Descriptors4", nestedfield="descriptors4", visible_pos=0),
        seeker.OptionFacet("emotion", label = "Emotion", nestedfield="emotion", visible_pos=0),
        seeker.OptionFacet("fragrattr", label = "Fragr Attr", nestedfield="fragrattr", visible_pos=0),
        seeker.OptionFacet("hedonics", label = "Hedonics", nestedfield="hedonics", visible_pos=0),
        seeker.OptionFacet("imagine", label = "imagine", nestedfield="imagine", visible_pos=0),
        seeker.OptionFacet("mood", label = "Mood", nestedfield="mood", visible_pos=0),
        seeker.OptionFacet("physical", label = "Physical", nestedfield="physical", visible_pos=0),
        seeker.OptionFacet("smell", label = "Smell", nestedfield="smell", visible_pos=0),
        seeker.OptionFacet("suitable_product", label = "Suitability Product", nestedfield="suitable_product", visible_pos=0),
        seeker.OptionFacet("suitable_stage", label = "Suitability Stage", nestedfield="suitable_stage", visible_pos=2),
        seeker.OptionFacet("fit_descriptors1", label = "Fit Descriptors1", nestedfield="fit_descriptors1", visible_pos=0),
        seeker.OptionFacet("fit_descriptors2", label = "Fit Descriptors2", nestedfield="fit_descriptors2", visible_pos=0),
        seeker.OptionFacet("fit_descriptors3", label = "Fit Descriptors3", nestedfield="fit_descriptors3", visible_pos=0),
        seeker.OptionFacet("fit_descriptors4", label = "Fit Descriptors4", nestedfield="fit_descriptors4", visible_pos=0),
        ]
    facets_keyword = [
        seeker.KeywordFacet("facet_keyword", label = "Benchmark", input="keywords_k"),
        ];
    #display = [
    #    "gender",
    #    "age",
    #    'brand',
    #    "blindcode",
    #    "freshness",
    #    ]
    exclude = [
        "resp_id",
        ]
    field_labels = {
        "question_p"    : "Question",
        }
    summary = [
        ]
    sumheader = ['brand']
    SUMMARY_URL="https://iffconnect.iff.com?id={0}"
    
    tabs = {'results_tab': '', 'summary_tab': 'hide', 'storyboard_tab': 'active', 'insights_tab': '' }
    decoder = None

    ### GLOBAL VARIABLES
             
scrape_li = []
posts_df = DataFrame()
molecules_d = {}
search_keywords = {}

scrape_q = queue.Queue()



