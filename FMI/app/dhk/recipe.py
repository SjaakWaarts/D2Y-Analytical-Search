"""
Definition of views.
"""

from django.shortcuts import render, redirect, render_to_response
from django.template.context_processors import csrf
#from django.core.urlresolvers import reverse
# django2.0
from django.urls import reverse
from django.http import HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import available_attrs
from functools import wraps
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import seeker
import json
import urllib
from datetime import datetime, time
import FMI.settings
import app.elastic as elastic
import app.scrape_ds as scrape_ds
import app.excitometer as excitometer
import app.sentiment as sentiment
import app.product as product
import app.market as market
import app.load as load
import app.crawl as crawl
import app.survey as survey
import app.guide as guide
import app.facts as facts
import app.r_and_d as r_and_d
import app.fmi_admin as fmi_admin
import app.azure as azure
import app.wb_excel as wb_excel
import app.models as models
import app.survey


def recipe_view(request):
    """Renders dhk page."""
    return render(
        request,
        'app/dhk/recipe.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

