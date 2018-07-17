"""
Definition of urls for FMI.
"""

from datetime import datetime
from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from app.forms import BootstrapAuthenticationForm
import app.views as views

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin
admin.autodiscover()

from django.contrib import auth

#params={'plugin': ModelSearchPlugin(MyModel), 'base_template': 'search.html'}
params={'plugin': '', 'base_template': 'search.html'}

import app.models as models
import app.views
import app.api
import seeker

#urlpatterns = patterns('',
urlpatterns = [
    # Examples:
    path('', app.views.home, name='home'),

    path('consumer_insight', app.views.consumer_insight_view, name='consumer_insight'),

    path('platform_admin', app.views.platform_admin_view, name='platform_admin'),
    path('crawl', app.views.crawl_view, name='crawl'),
    path('load', app.views.load_view, name='load'),
    path('facts', app.views.facts_view, name='facts'),
    path('fmi_admin', app.views.fmi_admin_view, name='fmi_admin'),


    path('scent_emotion', app.views.scent_emotion_view, name='scent_emotion'),
    path('search_scentemotion', models.ScentemotionSeekerView.as_view(), name='search_scentemotion'),
    path('search_studies', models.StudiesSeekerView.as_view(), name='search_studies'),

    path('product_insight', app.views.product_insight_view, name='product_insight'),
    path('search_pi/', models.PerfumeSeekerView.as_view(), name='search_pi'),
    path('product_elastic', app.product.ProductElasticView.as_view(), name='product_elastic'),
    path('r_and_d', app.views.r_and_d_view, name='r_and_d'),
    path('excitometer', app.views.excitometer_view, name='excitometer'),

    path('scrape', app.views.scrape_view, name='scrape'),

    path('api/storyboard_def', app.api.storyboard_def, name='api/storyboard_def'),
    path('api/site_menu', app.api.site_menu, name='api/site_menu'),
    path('api/conf_edit', app.api.conf_edit, name='api/conf_edit'),
    path('api/search_survey', app.api.search_survey, name='api/search_survey'),
    path('api/platformsearch', app.api.platformsearch, name='api/platformsearch'),
    path('api/scrape_pollresults', app.scrape_ds.scrape_pollresults_api, name='api/scrape_pollresults'),
    path('api/scrape_accords', app.api.scrape_accords_api, name='scrape_accords_api'),
    path('api/scrape_notes', app.api.scrape_notes_api, name='scrape_notes_api'),
    path('api/scrape_votes', app.api.scrape_votes_api, name='scrape_votes_api'),
    path('api/scrape_reviews', app.api.scrape_reviews_api, name='scrape_reviews_api'),

    #path('ingr_molecules', app.views.ingr_molecules, name='ingr_molecules'),
    path('search_workbook', app.views.search_workbook, name='search_workbook'),
    path('search_mi', models.PostSeekerView.as_view(), name='search_mi'),
    path('search_feedly', models.FeedlySeekerView.as_view(), name='search_feedly'),
    path('search_mail', models.MailSeekerView.as_view(), name='search_mail'),
    path('search_si_sites', models.PageSeekerView.as_view(), name='search_si_sites'),
    path('search_excel', models.ExcelSeekerView.as_view(), name='search_excel'),
    
    #re-path(r'search_survey/(?P<devise>[-\w]+)/$', models.SurveySeekerView.as_view(), name='search_survey'),
    path('search_survey', models.SurveySeekerView.as_view(), name='search_survey'),
    path('guide', app.views.guide_view, name='guide'),

    path('customer/', app.views.home, name='customer'),
    path('market_insight', app.views.market_insight_view, name='market_insight'),

    path('elastic/', app.views.elastic_view, name='elastic'),
    path('autocomplete/', app.views.autocomplete_view, name='autocomplete-view'),

    path('contact', app.views.contact, name='contact'),
    path('about', app.views.about, name='about'),

    # Registration URLs
    path('accounts/register/', views.register, name='register'),
    path('accounts/register_complete/', views.registrer_complete, name='register_complete'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('admin/', admin.site.urls),

    # Uncomment the admin/doc line below to enable admin documentation:
    #path('admin/doc/', include('django.contrib.admindocs.urls')),
    ]
#)