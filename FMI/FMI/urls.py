"""
Definition of urls for FMI.
"""

from datetime import datetime
#from django.conf.urls import patterns, include, url
from django.conf.urls import url
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
    url(r'^$', app.views.home, name='home'),

    url(r'^consumer_insight$', app.views.consumer_insight_view, name='consumer_insight'),

    url(r'^platform_admin', app.views.platform_admin_view, name='platform_admin'),
    url(r'^crawl', app.views.crawl_view, name='crawl'),
    url(r'^load', app.views.load_view, name='load'),
    url(r'^facts$', app.views.facts_view, name='facts'),
    url(r'^fmi_admin', app.views.fmi_admin_view, name='fmi_admin'),


    url(r'^scent_emotion/$', app.views.scent_emotion_view, name='scent_emotion'),
    url(r'^search_scentemotion$', models.ScentemotionSeekerView.as_view(), name='search_scentemotion'),
    url(r'^search_studies$', models.StudiesSeekerView.as_view(), name='search_studies'),

    url(r'^product_insight/$', app.views.product_insight_view, name='product_insight'),
    url(r'^search_pi/$', models.PerfumeSeekerView.as_view(), name='search_pi'),
    url(r'^product_elastic$', app.product.ProductElasticView.as_view(), name='product_elastic'),
    url(r'^r_and_d$', app.views.r_and_d_view, name='r_and_d'),
    url(r'^excitometer$', app.views.excitometer_view, name='excitometer'),

    url(r'^scrape', app.views.scrape_view, name='scrape'),

    url(r'^api/storyboard_def$', app.api.storyboard_def, name='api/storyboard_def'),
    url(r'^api/site_menu$', app.api.site_menu, name='api/site_menu'),
    url(r'^api/conf_edit$', app.api.conf_edit, name='api/conf_edit'),
    url(r'^api/search_survey$', app.api.search_survey, name='api/search_survey'),
    url(r'^api/platformsearch$', app.api.platformsearch, name='api/platformsearch'),
    url(r'^api/scrape_pollresults$', app.scrape_ds.scrape_pollresults_api, name='api/scrape_pollresults'),
    url(r'^api/scrape_accords$', app.api.scrape_accords_api, name='scrape_accords_api'),
    url(r'^api/scrape_notes$', app.api.scrape_notes_api, name='scrape_notes_api'),
    url(r'^api/scrape_votes$', app.api.scrape_votes_api, name='scrape_votes_api'),
    url(r'^api/scrape_reviews$', app.api.scrape_reviews_api, name='scrape_reviews_api'),

    #url(r'^ingr_molecules$', app.views.ingr_molecules, name='ingr_molecules'),
    url(r'^search_workbook$', app.views.search_workbook, name='search_workbook'),
    url(r'^search_mi$', models.PostSeekerView.as_view(), name='search_mi'),
    url(r'^search_feedly$', models.FeedlySeekerView.as_view(), name='search_feedly'),
    url(r'^search_mail$', models.MailSeekerView.as_view(), name='search_mail'),
    url(r'^search_si_sites/$', models.PageSeekerView.as_view(), name='search_si_sites'),
    url(r'^search_excel/$', models.ExcelSeekerView.as_view(), name='search_excel'),
    
    #url(r'^search_survey/(?P<devise>[-\w]+)/$', models.SurveySeekerView.as_view(), name='search_survey'),
    url(r'^search_survey$', models.SurveySeekerView.as_view(), name='search_survey'),
    url(r'^guide$', app.views.guide_view, name='guide'),

    url(r'^customer/$', app.views.home, name='customer'),
    url(r'^market_insight$', app.views.market_insight_view, name='market_insight'),

    url(r'^elastic/$', app.views.elastic_view, name='elastic'),
    url(r'^autocomplete/', app.views.autocomplete_view, name='autocomplete-view'),

    url(r'^contact$', app.views.contact, name='contact'),
    url(r'^about', app.views.about, name='about'),

    # Registration URLs
    url(r'^accounts/register/$', views.register, name='register'),
    url(r'^accounts/register_complete/$', views.registrer_complete, name='register_complete'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', admin.site.urls),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    ]
#)