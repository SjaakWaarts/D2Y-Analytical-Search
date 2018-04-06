from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import collections
from collections import OrderedDict

import seeker
import seeker.models
import elasticsearch_dsl as dsl
from elasticsearch_dsl.utils import AttrList, AttrDict

import app.models as models
import app.views
import app.survey as survey
import app.workbooks as workbooks
import app.wb_excel as wb_excel


# A site consists of tree of menu items pointing to a site item.
# A site item can be a data selecter: 

storyboard_link = workbooks.SurveyWorkbook.storyboard_link

site_views = {
    ## SELECTORS
    'age_sel' : {
        'type'      : 'selection',
        'descr'     : "Age",
        'filters'   : {'age.keyword' : []},
        'optionsmap'  : {},
        'selection' : 'facet',
        'selsize'   : '0-1',
        },
    #'category_sel' : {
    #    'type'      : 'selection',
    #    'descr'     : "Category",
    #    'filters'   : {'category.cat.keyword' : []},
    #    'selection' : 'images',
    #    'images'    : ['personalwash.jpg', 'homecare.jpg', 'fabriccare.jpg', 'haircare.jpg', 'toiletries.jpg'],
    #    'layout'    : 'grid-nx3',
    #    'listener'  : {'select' : {'select_event': 'category.cat.keyword'}},
    #    'optionsmap'  : {'Personal Wash': 'personalwash.jpg', 'Home Care': 'homecare.jpg', 'Fabric Care': 'fabriccare.jpg',
    #                     'Hair Care': 'haircare.jpg', 'Toiletries': 'toiletries.jpg'},
    #    'selsize'   : '0-1',
    #    'style'     :  {"height": "256", "width": "256"},
    #    },
    'category_sel' : {
        'type'      : 'selection',
        'descr'     : "Category",
        'filters'   : OrderedDict([('category.cat.keyword', []),('category.subcat.keyword', []) ]),
        'selection' : 'casc_images',
        'layout'    : 'grid-nx3',
        'optionsmap'  : {'category.cat.keyword': {
                            'root' : {'Personal Wash': 'personalwash.jpg', 'Home Care': 'homecare.jpg', 'Fabric Care': 'fabriccare.jpg',
                                    'Hair Care': 'haircare.jpg', 'Toiletries': 'toiletries.jpg'}
                            },
                        'category.subcat.keyword': {
                            'Personal Wash' : {'Personal Wash': 'personalwash.jpg', 'Home Care': 'homecare.jpg', 'Fabric Care': 'fabriccare.jpg'}
                            }
                        },
        'selsize'   : '1-n',
        'style'     :  {"height": "256", "width": "256"},
        },
    'consumer_sel' : {
        'type'      : 'answer_selection',
        'descr'     : "Consumer Attributes",
        'facet'     : 'perception.val.keyword',
        'filters'   : {'perception.val.keyword' : ["Elaborated","Richness","Balanced","Appetizing", "Recognizable"]},
        'listener'  : {'perception.val.keyword' : ["cand_perception_col"]},
        'selection' : 'facet',
        'selsize'   : '0-n',
        },
    'country_sel' : {
        'type'      : 'selection',
        'descr'     : "Country",
        'filters'   : {'country.keyword' : []},
        'selection' : 'graph',
        'url'       : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'link_filters',
        'dashboard_name' : 'link_filters_globe',
        # also hardcoded in the "country_map"
        'listener'    : {'select' : {'select_event': 'country_sel'}},
        'optionsmap'  : {},
        'selsize'   : '0-n',
        },
    'flavor_name_sel' : {
        'type'      : 'selection',
        'descr'     : "Tonality",
        'facet'     : 'flavor_name.keyword',
        'filters'   : {'flavor_name.keyword' : []},
        'selection' : 'facet',
        'selsize'   : '1',
        },
    'gender_sel' : {
        'type'      : 'selection',
        'descr'     : "Gender",
        'filters'   : {'gender.keyword' : []},
        'selection' : 'images',
        'images'    : ['male.jpg', 'female.jpg'],
        'layout'    : 'grid-nx2',
        'listener'  : {'select' : {'select_event': 'gender.keyword'}},
        'optionsmap'  : {'Female': 'female.jpg', 'Male': 'male.jpg'},
        'selsize'   : '0-1',
        'style'     :  {"height": "256", "width": "256"},
        },
    'mdt_country_sel' : {
        'type'      : 'selection',
        'descr'     : "Country",
        'filters'   : {'country.keyword' : []},
        'selection' : 'graph',
        'url'       : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_filters',
        'dashboard_name' : 'mdt_filters_globe',
        # also hardcoded in the "country_map"
        'listener'    : {'select' : {'select_event': 'mdt_country_sel'}},
        'optionsmap'  : {'GB': 'UK', 'USA' : 'United States'},
        'selsize'   : '0-n',
        },
    'panel_country_sel' : {
        'type'      : 'selection',
        'descr'     : "Country",
        'filters'   : {'country.keyword' : []},
        'selection' : 'graph',
        'url'       : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_filters',
        'dashboard_name' : 'panel_filters_globe',
        # also hardcoded in the "country_map"
        'listener'    : {'select' : {'select_event': 'panel_country_sel'}},
        'optionsmap'  : {'GB': 'UK', 'USA' : 'United States'},
        'selsize'   : '0-n',
        },
    'sensory_attr_sel' : {
        'type'      : 'answer_selection',
        'descr'     : "Sensory Attributes",
        'facet'     : 'sensory_attr.val.keyword',
        'filters'   : {'sensory_attr.val.keyword' : ["Meaty  HVP","Meaty Sulfury","Meaty Meaty"]},
        'listener'  : {'sensory_attr.val.keyword' : ["cand_sensory_attr_col"]},
        'selection' : 'facet',
        'selsize'   : '0-n',
        },
    'sensory_hedonics_sel' : {
        'type'      : 'answer_selection',
        'descr'     : "Sensory Hedonics",
        'facet'     : 'sensory_hedonics.val.keyword',
        'filters'   : {'sensory_hedonics.val.keyword' : ["Saltiness","Sweetness", "Umami"]},
        'listener'  : {'sensory_hedonics.val.keyword' : ["cand_sensory_hedonics_col"]},
        'selection' : 'facet',
        'selsize'   : '0-n',
        },
    'year_sel' : {
        'type'      : 'selection',
        'descr'     : "Year",
        'facet'     : 'published_date',
        'filters'   : {'published_date' : []},
        'selection' : 'facet',
        'selsize'   : '0-1',
        },
    ## LINK
    'portfolio-olfactive-map' : {
        'type'  : 'images',
        'descr' : "Portfolio Olfactive Map",
        'images': ["PORTFOLIO OLFACTIVE MAP_FABRIC CLEANING.jpg"],
        },
    'fragrance-passport' : {
        'type'  : 'carousels',
        'descr' : "Fragrance Pasport",
        'carousels' : [
            ("Aragon", ["ARAGON INFORMATION.jpg", "ARAGON PERFORMANCE.jpg", "ARAGON THEME.jpg"]),
            ("Blue Legend", ["BLUE LEGEND INFORMATION.jpg", "BLUE LEGEND PERFORMANCE.jpg", "BLUE LEGEND THEME.jpg"]),
            ]},
    'project-mona-lisa' : {
        'type'  : 'carousels',
        'descr' : "Project (Mona Lisa)",
        'carousels' : [
            ("Project", ["123513WRB_project.jpg", "123513WRB_objective.jpg", "123513WRB_success.jpg"]),
            ("CI - task", ["123513WRB_decoder.jpg", "123513WRB_questionnaire.jpg"]),
            ]},
    'fabric_conditioners' : {
        'type'  : 'facets_image',
        'descr' : "Fabric Conditioners",
        'facets': ['country', 'brand']},
    'powder_detergents' : {
        'type'  : 'facets_image',
        'descr' : "Powder Detergents",
        'facets': ['country', 'brand']},
    'liquid_detergents' : {
        'type'  : 'facets_image',
        'descr' : "Liquid Detergents",
        'facets': ['country', 'brand']},
    'hedonics_overall' : {
        'type'  : 'charts',
        'descr' : "Hedonics Overall",
        'url'   : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'initial',
        'dashboard_name' : 'Topline',
        'tiles' : []},
    'hedonics_per_format' : {
        'type'  : 'charts',
        'descr' : "Hedonics Per Format",
        'url'   : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'initial',
        'dashboard_name' : 'Hedonics',
        'tiles' : [{'field': 'product_form.keyword', 'layout' : 'rows'} ]},
    'driver_of_liking' : {
        'type'  : 'charts',
        'descr' : "Driver of Liking",
        'url'   : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'initial',
        'dashboard_name' : 'Driver Liking',
        'tiles' : [{'field': 'product_form.keyword', 'layout' : 'dropdown'} ]},
    'intensity' : {
        'type'  : 'charts',
        'descr' : "Intensiy",
        'url'   : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'initial',
        'dashboard_name' : 'Intensity',
        'tiles' : []},
    'fresh' : {
        'type'  : 'charts',
        'descr' : "Fresh",
        'url'   : '/search_survey?',
        'workbook_name' : 'link',
        'storyboard_name' : 'initial',
        'dashboard_name' : 'Fresh',
        'tiles' : []},
    'superior_fresh' : {
        'type'  : 'drivers',
        'descr' : "Superior Fresh",
        'drivers': ['freshness''method']},
    'clean' : {
        'type'  : 'drivers',
        'descr' : "Clean",
        'drivers': ['cleanness''method']},
    'long_lasting' : {
        'type'  : 'drivers',
        'descr' : "Long Lasting",
        'drivers': ['lastingness''method']},
    'fresh_cluster' : {
        'type'  : 'cluster',
        'descr' : "Cluster",
        'drivers': ['lastingness''method']},
    'fresh_sensorial_revitalizing' : {
        'type'  : 'charts',
        'descr' : "Freshness Model Sensorial And Revitalizing",
        'charts': ['sensorial_freshness_bar', 'revitalizing_freshness_bar']},
    'fresh_essential_confident' : {
        'type'  : 'charts',
        'descr' : "Freshness Model Essential And Confident",
        'charts': ['essential_freshness_bar', 'confident_freshness_bar']},
    'newness_model' : {
        'type'  : 'quadrant',
        'descr' : "Newness Model",
        'quadrants':[('Cult', 'complex/familair'), ('Intrigue', 'complex/unfamilair'),
                     ('Legend','simple/familair'), ('Broad Appeal''simple/unfamilair')],
        'facets': ['uniqueness', 'complexity']},
    'most_often_users' : {
        'type'  : 'top-n',
        'descr' : "Most Often Users",
        'n'     : "8",
        'tile'  : 'format',
        'facets': ['freshness''superior', 'cleanness', 'lastingness']},
    'fresh_chart' : {
        'type'  : 'charts',
        'descr' : "Chart",
        'charts': ['ness_line']},
    'fresh_summary' : {
        'type'  : 'carousels',
        'descr' : "Country Summary",
        'carousels' : [
            ("Brazil", ["fresh_summary_Brazil.png"]),
            ("China", ["fresh_summary_China.png"]),
            ("India", ["fresh_summary_India.png"]),
            ("Indonesia", ["fresh_summary_Indonesia.png"]),
            ("Nigeria", ["fresh_summary_Nigeria.png"]),
            ("Brazil", ["fresh_summary_Brazil.png"]),
            ("SouthAfrica", ["fresh_summary_SouthAfrica.png"]),
            ("Thailand", ["fresh_summary_Thailand.png"]),
            ("Turkey", ["fresh_summary_Turkey.png"]),
            ("UK", ["fresh_summary_UK.png"]),
            ("Vietnam", ["fresh_summary_Vietnam.png"]),
            ]},
    'format_total' : {
        'type'  : 'tiled_chart',
        'descr' : "Total",
        'tile'  : 'format',
        'chart' : 'cand_hedonics_col'},
    'format_brand' : {
        'type'  : 'top-n',
        'descr' : "Brand",
        'n'     : "5",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'format_split' : {
        'type'  : 'top-n',
        'descr' : "User Split",
        'n'     : "5",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'perfume_driven' : {
        'type'  : 'top-n',
        'descr' : "Perfume Driven",
        'n'     : "4",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'sensitive_care' : {
        'type'  : 'top-n',
        'descr' : "Sensitive Care",
        'n'     : "4",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'functionailty' : {
        'type'  : 'top-n',
        'descr' : "Functionailty",
        'n'     : "4",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'extra_benefits' : {
        'type'  : 'top-n',
        'descr' : "Extra_Benefits",
        'n'     : "4",
        'tiles' : ['method', 'suitability', 'brand'],
        'facets': ['candidates']},
    'cross_fabrics' : {
        'type'  : 'metric_chart',
        'descr' : "Cross Fabrics",
        'metrics': ['hedonics', 'freshness', 'cleanness', 'lastingness'],
        'chart' : 'globe_chart'},
    'fabric_conditioner' : {
        'type'  : 'metric_chart',
        'descr' : "Fabric Conditioner",
        'metrics': ['hedonics', 'freshness', 'cleanness', 'lastingness'],
        'chart' : 'globe_chart'},
    'detergents' : {
        'type'  : 'metric_chart',
        'descr' : "Detergents",
        'metrics': ['hedonics', 'freshness', 'cleanness', 'lastingness'],
        'chart' : 'globe_chart'},
    'topline_tables' : {
        'type'  : 'metric_chart',
        'descr' : "Top Line Tables",
        'metrics': ['hedonics', 'freshness', 'cleanness', 'lastingness'],
        'chart' : 'globe_chart'},
    ## MDT
    'mdt_tools' : {
        'type'  : 'carousels',
        'descr' : "Modular Design Tools",
        'carousels' : [
            ("Modular Design Tools", ["mdt_relevance.jpg", "mdt_market_brief.jpg", "mdt_cfd_core_formulation_design.jpg"]),
            ("Predictive Desing Platform", ["mdt_desing_platform.jpg", "mdt_cfd_strategy.jpg"]),
            ]},
    'mdt_consumer' : {
        'type'  : 'charts',
        'descr' : "Consumer",
        'url'   : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_consumer',
        'dashboard_name' : 'mdt_consumer',
        'tiles' : []},
    'mdt_sensory' : {
        'type'  : 'charts',
        'descr' : "Sensory",
        'url'   : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_sensory',
        'dashboard_name' : 'mdt_sensory',
        'tiles' : []},
    'mdt_profile_taste' : {
        'type'  : 'charts',
        'descr' : "Profile Taste",
        'url'   : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_profile',
        'dashboard_name' : 'mdt_profile_taste',
        'tiles' : []},
    'mdt_profile_smell' : {
        'type'  : 'charts',
        'descr' : "Profile Smell",
        'url'   : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_profile',
        'dashboard_name' : 'mdt_profile_smell',
        'tiles' : []},
    'mdt_insights' : {
        'type'  : 'charts',
        'descr' : "Insights",
        'url'   : '/search_workbook?',
        'workbook_name' : 'sensory',
        'storyboard_name' : 'mdt_insights',
        'dashboard_name' : 'mdt_insights',
        'tiles' : []},
    ## PANEL
    'panel_onepager' : {
        'type'  : 'charts',
        'descr' : "One Pager",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_onepager',
        'dashboard_name' : 'panel_onepager',
        'tiles' : []},
    'panel_onepager_ttest' : {
        'type'  : 'charts',
        'descr' : "t-test",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_onepager',
        'dashboard_name' : 'panel_onepager_ttest',
        'tiles' : []},
    'panel_liking_perc' : {
        'type'  : 'charts',
        'descr' : "Liking %",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_liking',
        'dashboard_name' : 'panel_liking_perc',
        'tiles' : []},
    'panel_liking_count' : {
        'type'  : 'charts',
        'descr' : "Liking #",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_liking',
        'dashboard_name' : 'panel_liking_count',
        'tiles' : []},
    'panel_topline' : {
        'type'  : 'charts',
        'descr' : "Topline",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_liking',
        'dashboard_name' : 'panel_topline',
        'tiles' : []},
    'panel_topic_hedonics' : {
        'type'  : 'charts',
        'descr' : "Hedonics",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_hedonics',
        'tiles' : []},
    'panel_topic_attributes' : {
        'type'  : 'charts',
        'descr' : "Attributes",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_attributes',
        'tiles' : []},
    'panel_topic_platform' : {
        'type'  : 'charts',
        'descr' : "Platform",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_platform',
        'tiles' : []},
    'panel_topic_benefits' : {
        'type'  : 'charts',
        'descr' : "Benefits",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_benefits',
        'tiles' : []},
    'panel_topic_olfactive_attr' : {
        'type'  : 'charts',
        'descr' : "Olfactive",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_olfactive_attr',
        'tiles' : []},
    'panel_topic_color' : {
        'type'  : 'charts',
        'descr' : "Color",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_color',
        'tiles' : []},
    'panel_topic_newness' : {
        'type'  : 'charts',
        'descr' : "Newness",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_topic',
        'dashboard_name' : 'panel_topic_newness',
        'tiles' : []},
    'panel_stats_emotion' : {
        'type'  : 'charts',
        'descr' : "Emotion",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_stats',
        'dashboard_name' : 'panel_stats_emotion',
        'tiles' : []},
    'panel_stats_benefits' : {
        'type'  : 'charts',
        'descr' : "Benefits",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_stats',
        'dashboard_name' : 'panel_stats_benefits',
        'tiles' : []},
    'panel_stats_olfactive_attr' : {
        'type'  : 'charts',
        'descr' : "Olfactive",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_stats',
        'dashboard_name' : 'panel_stats_olfactive_attr',
        'tiles' : []},
    'panel_profile_emotion' : {
        'type'  : 'charts',
        'descr' : "Emotion",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_profile',
        'dashboard_name' : 'panel_profile_emotion',
        'tiles' : []},
    'panel_profile_benefits' : {
        'type'  : 'charts',
        'descr' : "Benefits",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_profile',
        'dashboard_name' : 'panel_profile_benefits',
        'tiles' : []},
    'panel_profile_olfactive_attr' : {
        'type'  : 'charts',
        'descr' : "Olfactive",
        'url'   : '/search_survey?',
        'workbook_name' : 'global panels',
        'storyboard_name' : 'panel_profile',
        'dashboard_name' : 'panel_profile_olfactive_attr',
        'tiles' : []},
    }

link_menu_items = {
    'Globe' : {
        'type'  : 'data-selector',
        'view'  : 'country_sel',
        },
    'Gender' : {
        'type'  : 'data-selector',
        'view'  : 'gender_sel',
        },
    'Age' : {
        'type'  : 'data-selector',
        'view'  : 'age_sel',
        },
    'Fragrance Passport' : {
        'type'  : 'view-selector',
        'views' : ['portfolio-olfactive-map', 'fragrance-passport'],
        'style' :  {"background-image": "url('/static/app/media/link/correlation.jpg')", "background-size": "cover"},
        },
    'Washing Habits' : {
        'type'  : 'wip'},
    'Performance' : {
        'type'  : 'wip'},
    'Brands' : {
        'type'  : 'view-selector',
        'views' : ['fabric_conditioners', 'powder_detergents', 'liquid_detergents'],
        'style' :  {"background-image": "url('/static/app/media/link/correlation.jpg')", "background-size": "cover"},
        },
    'Liking' : {
        'type'  : 'view-selector',
        'views' : ['hedonics_overall', 'hedonics_per_format', 'intensity', 'driver_of_liking'],
        'style' :  {"background-image": "url('/static/app/media/link/likingbg.jpg')", "background-size": "cover"},
        },
    'Freshness' : {
        'type'  : 'view-selector',
        'views' : ['fresh', 'superior_fresh', 'clean', 'long_lasting', 'fresh_cluster',
                   'fresh_sensorial_revitalizing', 'fresh_essential_confident',
                   'newness_model', 'most_often_users', 'fresh_chart', 'fresh_summary'],
        'style' :  {"background-image": "url('/static/app/media/link/freshnessbg.jpg')", "background-size": "cover"},
        },
    'Format Suitability' : {
        'type'  : 'view-selector',
        'views' : ['format_total', 'format_brand', 'format_split']},
    'Benefits' : {
        'type'  : 'view-selector',
        'views' : ['perfume_driven', 'sensitive_care', 'functionailty', 'extra benefits']},
    'Correlation' : {
        'type'  : 'view-selector',
        'views' : ['cross_fabrics', 'fabric_conditioner', 'detergents']},
    'Top Line Tables' : {
        'type'  : 'site_view',
        'view'  : 'topline_tables'},
    }

link_menu = {
    'menu'  : ['Globe', 'Gender', 'Age', 'Fragrance Passport', 'Washing Habits', 'Performance', 'Brands', 'Liking',
               'Freshness', 'Format Suitability', 'Benefits', 'Correlation', 'Top Line Tables'],
    'menu_items'    : link_menu_items
    }


panel_menu_items = {
    'Year' : {
        'type'  : 'data-selector',
        'view'  : 'year_sel',
        },
    'Category' : {
        'type'  : 'data-selector',
        'view'  : 'category_sel',
        },
    'Globe' : {
        'type'  : 'data-selector',
        'view'  : 'panel_country_sel',
        },
    'Gender' : {
        'type'  : 'data-selector',
        'view'  : 'gender_sel',
        },
    'Age' : {
        'type'  : 'data-selector',
        'view'  : 'age_sel',
        },
    'CRP' : {
        'type'  : 'view-selector',
        'views' : ['project-mona-lisa', 'portfolio-olfactive-map', 'fragrance-passport'],
        'style' :  {"background-image": "url('/static/app/media/link/correlation.jpg')", "background-size": "cover"},
        },
    'One Pager' : {
        'type'  : 'view-selector',
        'views' : ['panel_onepager', 'panel_onepager_ttest'],
        'style' :  {"background-image": "url('/static/app/media/link/likingbg.jpg')", "background-size": "cover"},
        },
    'Hedonics' : {
        'type'  : 'view-selector',
        'views' : ['panel_liking_perc', 'panel_liking_count', 'panel_topline'],
        'style' :  {"background-image": "url('/static/app/media/link/likingbg.jpg')", "background-size": "cover"},
        },
    'Topic' : {
        'type'  : 'view-selector',
        'views' : ['panel_topic_hedonics', 'panel_topic_attributes', 'panel_topic_platform', 'panel_topic_benefits',
                   'panel_topic_olfactive_attr', 'panel_topic_color',  'panel_topic_newness'],
        'style' :  {"background-image": "url('/static/app/media/link/freshnessbg.jpg')", "background-size": "cover"},
        },
    'Stats' : {
        'type'  : 'view-selector',
        'views' : ['panel_stats_emotion', 'panel_stats_benefits', 'panel_stats_olfactive_attr'],
        'style' :  {"background-image": "url('/static/app/media/link/freshnessbg.jpg')", "background-size": "cover"},
        },
    'Profile' : {
        'type'  : 'view-selector',
        'views' : ['panel_profile_emotion', 'panel_profile_benefits', 'panel_profile_olfactive_attr'],
        'style' :  {"background-image": "url('/static/app/media/link/correlation.jpg')", "background-size": "cover"},
        },
    }

panel_menu = {
    'menu'  : ['Category', 'Year', 'Globe', 'Gender', 'Age', 'CRP', 'One Pager', 'Hedonics', 'Topic', 'Stats', 'Profile'],
    'menu_items'    : panel_menu_items
    }


mdt_menu_items = {
    'Category' : {
        'type'  : 'data-selector',
        'view'  : 'category_sel',
        },
    'Globe' : {
        'type'  : 'data-selector',
        'view'  : 'mdt_country_sel',
        },
    'Tonality' : {
        'type'  : 'data-selector',
        'view'  : 'flavor_name_sel',
        },
    'Consumer Attributes' : {
        'type'  : 'data-selector',
        'view'  : 'consumer_sel',
        },
    'Sensory Attributes' : {
        'type'  : 'data-selector',
        'view'  : ['sensory_attr_sel','sensory_hedonics_sel'],
        #'view'  : 'sensory_attr_sel',
        },
    'MDT' : {
        'type'  : 'view-selector',
        'views' : ['mdt_tools'],
        'style' :  {"background-image": "url('/static/app/media/link/correlation.jpg')", "background-size": "cover"},
        },
    'Consumer' : {
        'type'  : 'view-selector',
        'views' : ['mdt_consumer'],
        'style' :  {"background-image": "url('/static/app/media/link/likingbg.jpg')", "background-size": "cover"},
        },
    'Sensory' : {
        'type'  : 'view-selector',
        'views' : ['mdt_sensory'],
        'style' :  {"background-image": "url('/static/app/media/link/likingbg.jpg')", "background-size": "cover"},
        },
    'Profile' : {
        'type'  : 'view-selector',
        'views' : ['mdt_profile_taste', 'mdt_profile_smell'],
        'style' :  {"background-image": "url('/static/app/media/link/freshnessbg.jpg')", "background-size": "cover"},
        },
    'Insights' : {
        'type'  : 'view-selector',
        'views' : ['mdt_insights'],
        'style' :  {"background-image": "url('/static/app/media/link/freshnessbg.jpg')", "background-size": "cover"},
        },
    }

mdt_menu = {
    'menu'  : ['Category', 'Globe', 'Tonality', 'Consumer Attributes', 'Sensory Attributes', 'MDT', 'Consumer', 'Sensory', 'Profile', 'Insights'],
    'menu_items'    : mdt_menu_items
    }

sites = OrderedDict([
    ('link', {
        'type'  : 'site',
        'descr' : 'LiNK',
        'site_menu': link_menu
        }),
    ('panels', {
        'type'  : 'site',
        'descr' : 'Panels',
        'site_menu': panel_menu
        }),
    ('mdt', {
        'type'  : 'site',
        'descr' : 'Modular Design Tool',
        'site_menu': mdt_menu,
        'workbook_name': 'sensory'
        })
    ])

# A guide consists of routes and a route consists of steps. A route leads to the destination.
# A step is selection or decision that has to be made to lead to the end resulst.


country2geochart = {
    'UK'    : 'GB',
    'USA'   : 'United States'
    }

#category_gallery = [
#    ('Female', '/static/app/media/female.jpg'),
#    ('Male', '/static/app/media/male.jpg'),
#    ]

#gender_gallery = [
#    ('Female', '/static/app/media/female.jpg'),
#    ('Male', '/static/app/media/male.jpg'),
#    ]


#dataset_gallery = [
#    ('CI Survey', '/static/app/media/CI2.jpg'),
#    ('SE Studies', '/static/app/media/CFT_CI.jpg'),
#    ('SDM', '/static/app/media/SDM.jpg'),
#    ]

#steps = {
#    'age_sel' : {
#        'type'      : 'selection',
#        'facet'     : 'age.keyword',
#        'selection' : ('facet', 'terms'),
#        'selsize'   : '0-1',
#        },
#    'country_sel' : {
#        'type'      : 'selection',
#        'facet'     : 'country.keyword',
#        #'selection' : ('graph', storyboard['country_sel'], charts),
#        'selection' : ('graph', workbooks.SurveyWorkbook.storyboard_link_filters[0],
#                                workbooks.SurveyWorkbook.dashboard_link),
#        'selsize'   : '0-n',
#        },
#    'gender_sel' : {
#        'type'      : 'selection',
#        'facet'     : 'gender.keyword',
#        'selection' : ('gallery', gender_gallery),
#        'selsize'   : '0-1',
#        },
#    'dataset_dec' : {
#        'type'      : 'decision',
#        'select'    : 'dataset_dec',
#        'selection' : ('gallery', dataset_gallery),
#        'selsize'   : '1',
#        'decisionstep' : {
#            'Fresh and Clean'   : 'fresh_and_clean_profile_dest',
#            'Orange Beverages'  : 'orange_bevarages_profile_dest',
#            'SE Studies'        : 'studies_profile_dest',
#            'SDM'               : 'SDM_storyboard_dest'}
#        },
#    'fresh_and_clean_profile_dest'   : {
#        'type'      : 'destination',
#        'url'       : '/search_survey?workbook_name=fresh+and+clean&survey.keyword=fresh+and+clean',
#        'seeker'    : 'SurveySeekerView',
#        'tab'       : 'storyboard',
#        'dashboard' : 'profile',
#        },
#    'orange_bevarages_profile_dest'   : {
#        'type'      : 'destination',
#        'url'       : '/search_survey?workbook_name=orange+beverages&survey.keyword=orange+beverages',
#        'seeker'    : 'SurveySeekerView',
#        'tab'       : 'storyboard',
#        'dashboard' : 'profile',
#        },
#    'studies_profile_dest'   : {
#        'type'      : 'destination',
#        'url'       : '/search_studies',
#        'seeker'    : 'StudiesSeekerView',
#        'tab'       : 'storyboard',
#        'dashboard' : 'profile',
#        },
#    'SDM_storyboard_dest'   : {
#        'type'      : 'destination',
#        'url'       : '/search_survey',
#        'seeker'    : 'SurveySeekerView',
#        'tab'       : 'AJAX',
#        'dashboard' : 'profile',
#        },
#    }

#routes = {
#    'route_sdm' : ('SurveySeekerView',
#                  ['country_sel', 'gender_sel', 'age_sel', 'dataset_dec']),
#    'route_ci_fresh' : ('SurveySeekerView',
#                   ['fresh_and_clean_profile_dest']),
#    'route_ci_oranges' : ('SurveySeekerView',
#                   ['orange_bevarages_profile_dest']),
#    }

#guide = {
#    'routes'        : routes,
#    'steps'         : steps,
#    }

site2seeker = {
    'link'          : (models.SurveySeekerView, 'link'),
    'panels'        : (models.SurveySeekerView, 'global panels'),
    'mdt'           : (models.ExcelSeekerView, 'sensory'),
    'route_ci'      : (models.SurveySeekerView, ''),
    'route_sdm'     : (models.SurveySeekerView, ''),
    'SurveySeekerView' : (models.SurveySeekerView, ''),
    'StudiesSeekerView' : (models.StudiesSeekerView, ''),
    }


def country_map_geochart(country):
    global country2geochart

    if country in country2geochart:
        geo_country = country2geochart[country]
    else:
        geo_country = country
    return geo_country


#def step_filter(search, facets, step):
#    facet_field = step['facet']
#    for facet in facets:
#        if facet.field == facet_field:
#            break
#    values = facets[facet]
#    search = facet.filter(search, values)
#    return search

#def step_aggr(search, facets, step):
#    facet_field = step['facet']
#    for facet in facets:
#        if facet.field == facet_field:
#            break
#    aggr_stack = {}
#    search = facet.apply(search, facet.name, aggr_stack)
#    return search

## prepare the data for the selected route
#def route_step(request, tiles_d, route_name, step_name):
#    route = routes[route_name]
#    route_steps = route[1]
#    seekerview = site2seeker[route_name][0]()
#    seekerview.request = request
#    facets = seekerview.get_facet_selected_data()
#    seekerview.set_workbook_filters(facets, workbooks.SurveyWorkbook.workbooks['link'])
#    using = seekerview.using
#    index = seekerview.index
#    search = seekerview.document.search().index(index).using(using).extra(track_scores=True)

#    stepnr = 0;
#    while stepnr < len(route_steps):
#        step = steps[route_steps[stepnr]]
#        if step['type'] == 'selection':
#            search = step_filter(search, facets, step)
#            search = step_aggr(search, facets, step)
#        stepnr = stepnr + 1

#    results = {}
#    step = steps[step_name]
#    if step['type'] == 'selection':
#        search = step_aggr(search, facets, step)
#        results = search.execute(ignore_cache=True)
#        route_charts = {}
#        if step['selection'][0] == 'graph':
#            dashboard_layout = step['selection'][1]['layout']
#            for key, map in dashboard_layout.items():
#                for row in map:
#                    for chart_name in row:
#                        tiles_d[chart_name] = {}
#                        chart = step['selection'][2][chart_name]
#                        data_type = chart['data_type']
#                        if data_type == 'facet':
#                            chart_data, meta_data = seeker.dashboard.bind_facet(seekerview, chart, results.aggregations)
#                        if data_type == 'aggr':
#                            chart_data, meta_data = seeker.dashboard.bind_aggr(seekerview, chart, chart_name, results.aggregations)
#                        if chart['chart_type'] == 'GeoChart':
#                            for row in chart_data:
#                                row[0] = country_map_geochart(row[0])
#                        tiles_d[chart_name]['All'] = {'chart_data' : chart_data, 'meta_data' : meta_data}
#    if step['type'] == 'decision':
#        results = search.execute(ignore_cache=True)
#    if step['type'] == 'destination':
#        results = search.execute(ignore_cache=True)

#    for facet in list(facets):
#        stepix = 0;
#        found = False
#        while stepix < len(route_steps):
#            step = steps[route_steps[stepix]]
#            if step['type'] == 'selection':
#                for filter_field in step['filters'].keys():
#                    if filter_field == facet.field:
#                        found = True
#            stepix = stepix + 1
#        if not found :
#            del facets[facet]

#    return results, facets

## destination reached
#def route_dest(request, route_name, step_name):
#    route = routes[route_name]
#    route_steps = route[1]
#    step = steps[step_name]
#    if step['type'] == 'decision':
#        decision = request.GET[step_name]
#        dest_step_name = step['decisionstep'][decision]
#        step_name = dest_step_name
#    return step_name


def site_menu_search(request, site_name):
    site = sites[site_name]
    site_menu = site['site_menu']
    menu_items = site_menu['menu_items']

    seekerview = site2seeker[site_name][0]()
    workbook_name = site2seeker[site_name][1]
    seekerview.request = request
    seekerview.aggs_stack = None
    seekerview.aggs_stack = {}
    if type(seekerview) == models.SurveySeekerView:
        facets = seekerview.get_facet_selected_data()
        seekerview.set_workbook_filters(facets, workbooks.SurveyWorkbook.workbooks[workbook_name])
    elif type(seekerview) == models.ExcelSeekerView:
        app.views.set_workbook(workbook_name)
        facets = seekerview.get_facet_selected_data()
        seekerview.set_workbook_filters(facets, wb_excel.workbooks[workbook_name])
    using = seekerview.using
    index = seekerview.index

    search = seekerview.document.search().index(index).using(using).extra(track_scores=True)
    search, keywords_q = seekerview.get_search(keywords_q=None, facets=facets, facets_keyword=None, dashboard=None, aggregate=True)
    #search = self.get_aggr(search, self.dashboard)
    #results = search.execute(ignore_cache=True)
    results = seeker.elastic_get(seekerview.index, '_search', search.to_dict())
    aggregations = results.get('aggregations', {})

    #copy to list because facets is changed
    for facet in list(facets):
        facet_filters = facets[facet]
        found_view = None
        for name, item in menu_items.items():
            menu_item = menu_items[name]
            if menu_item['type'] == 'data-selector':
                if type(menu_item['view']) == list:
                    view_names = menu_item['view']
                else:
                    view_names = [menu_item['view']]
                for view_name in view_names:
                    view = site_views[view_name]
                    for filter_field in view['filters'].keys():
                        if filter_field == facet.field:
                            if view['type'] == 'selector': # not for answer selectors!
                                view['filters'][filter_field] = facet_filters
                            found_view = view
                            break
        if found_view is None:
            del facets[facet]
        else:
            facet_values = {}
            if facet.field in aggregations:
                optionsmap = found_view.get('optionsmap', {})
                if found_view['selection'] in ['images', 'facet', 'graph']:
                    xfacet = seekerview.get_facet_by_field_name(facet.field)
                    aggr = aggregations[facet.field]
                    buckets = xfacet.buckets(aggr)
                    # first add missing facet values
                    #for bucket in aggregations[facet.field]['buckets']:
                    for X_key, bucket in buckets.items():
                        facet_value = bucket.get('key_as_string', bucket.get('key'))
                        facet_values[facet_value] = facet_value
                        if facet_value not in optionsmap:
                            optionsmap[facet_value] = facet_value
                    # next delete options which aren't selected anymore
                    for option in list(optionsmap.keys()):
                        if option not in facet_values:
                            del optionsmap[option]
                    found_view['optionsmap'] = optionsmap
                if found_view['selection'] == 'casc_images':
                    # to be implemented in combination with casc_facet type
                    pass
                     



    return results, facets

# prepare the data for the selected menu for the site
def site_menu(request, site_name, menu_name, view_name, tile_facet_field):
    results, facets = site_menu_search(request, site_name)
    site = sites[site_name]
    site_menu = site['site_menu']
    menu_items = site_menu['menu_items']
    for name, item in menu_items.items():
        menu_item = menu_items[name]
        if menu_item['type'] == 'data-selector':
            #route_name = menu_item['step'][0];
            #step_name = menu_item['step'][1];
            #results, facets = route_step(request, tiles_d, route_name, step_name);
            pass
        elif menu_item['type'] == 'view-selector':
            if view_name != '':
                site_view = site_views[view_name]
                if 'tiles' in site_view:
                    if (tile_facet_field != '' and tile_facet_field != 'All'):
                        if len(site_view['tiles']) > 0:
                            tile = site_view['tiles'][0]
                            tile['field'] = tile_facet_field
                        else:
                            tile = {'field': tile_facet_field, 'layout' : 'dropodown'}
                            site_view['tiles'].append(tile)
                    if (tile_facet_field == 'All') and len(site_view['tiles']) > 0:
                        site_view['tiles'] = []
        else:
            pass
    return results, facets

