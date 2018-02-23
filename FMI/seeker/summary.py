from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse, QueryDict, Http404
from django.shortcuts import render, redirect
from django.template import loader, Context, RequestContext
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.generic import View
from elasticsearch_dsl.utils import AttrList
#from seeker.templatetags.seeker import seeker_format
from app.templatetags.seeker import seeker_format
from .mapping import DEFAULT_ANALYZER
import collections
import elasticsearch_dsl as dsl
import inspect
import six
import urllib
import re
import string
from collections import OrderedDict

def is_common(ngram):
    commonwords = [
        'the', 'be', 'and', 'of', 'a', 'in', 'to', 'have', 'it',
        'i', 'that', 'for', 'you', 'he', 'with', 'on', 'do', 'say', 'this',
        'they', 'us', 'an', 'at', 'but', 'we', 'his', 'from', 'that', 'not',
        'by', 'she', 'or', 'as', 'what', 'go', 'their', 'can', 'who', 'get',
        'if', 'would', 'her', 'all', 'my', 'make', 'about', 'know', 'will',
        'as', 'up', 'one', 'time', 'has', 'been', 'there', 'year', 'so',
        'think', 'when', 'which', 'then', 'some', 'me', 'people', 'take',
        'out', 'into', 'just', 'see', 'him', 'your', 'come', 'could', 'now',
        'than', 'like', 'other', 'how', 'then', 'its', 'our', 'two', 'more',
        'these', 'want', 'way', 'look', 'first', 'also', 'new', 'because',
        'day', 'more', 'use', 'no', 'man', 'find', 'here', 'thing', 'give', 
        'many', 'well'
        ]
    for word in ngram:
        if word in commonwords:
            return True
    return False

def clean_input(input):
    input = re.sub('\n+', " ", input)       #replace nl with a space
    input = re.sub('\[[0-9]*\]', "", input) #discard citation marks
    input = re.sub(' +', " ", input)        #replace multiple spaces with a sigle space
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    input = regex.sub(" ", input)           #replace punctuations with a sigle space
    input = bytes(input, "UTF-8")           #remove unicode characters
    input = input.decode("ascii", "ignore")
    input = input.split(' ')
    words = []
    for item in input:
        item = item.strip(string.punctuation)
        if len(item) > 1 or (item.lower() == 'a' or item.lower() == 'i'):
            words.append(item)
    return words


def get_ngrams(input, n):
    input = clean_input(input)
    output = {}
    for i in range(len(input)-n+1):
        newngram = input[i:i+n]
        if not is_common(newngram):
            newngram = " ".join(newngram)
            if newngram in output:
                output[newngram] = output[newngram] + 1
            else:
                output[newngram] = 1
    ngrams = OrderedDict(sorted(output.items(), key=lambda t: t[1], reverse=True))
    return ngrams