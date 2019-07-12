"""
Definition of dhk-views.
"""

from datetime import datetime
import re
import sys
import os
import shutil
import json
import urllib
import requests
from slugify import slugify
from io import BytesIO
import zipfile
import docx
from docx.table import _Cell, Table
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
import seeker.esm as esm
from FMI.settings import BASE_DIR, ES_HOSTS






