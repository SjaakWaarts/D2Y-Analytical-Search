import pandas as pd
import numpy as np
import queue
from django.core.files import File
import glob, os
import pickle
import json
from urllib.request import urlopen
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from selenium import webdriver
import time
from datetime import datetime

import app.models as models

# driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe')


##!/usr/bin/env ruby

#require 'time'
#require 'uri'
#require 'openssl'
#require 'base64'

## Your AWS Access Key ID, as taken from the AWS Your Account page
#AWS_ACCESS_KEY_ID = "AKIAJCJSPWI2LEMW5ILA"

## Your AWS Secret Key corresponding to the above ID, as taken from the AWS Your Account page
#AWS_SECRET_KEY = "x3jO6YZzaKWzbtz+3EpLcc3LYkO9nWXUekEzzBcy"

## The region you are interested in
#ENDPOINT = "webservices.amazon.com"

#REQUEST_URI = "/onca/xml"

#params = {
#  "Service" => "AWSECommerceService",
#  "Operation" => "ItemSearch",
#  "AWSAccessKeyId" => "AKIAJCJSPWI2LEMW5ILA",
#  "AssociateTag" => "doubleyou00-20",
#  "SearchIndex" => "Beauty",
#  "Keywords" => "joop",
#  "ResponseGroup" => "Reviews",
#  "Sort" => "price"
#}

## Set current timestamp if not set
#params["Timestamp"] = Time.now.gmtime.iso8601 if !params.key?("Timestamp")

## Generate the canonical query
#canonical_query_string = params.sort.collect do |key, value|
#  [URI.escape(key.to_s, Regexp.new("[^#{URI::PATTERN::UNRESERVED}]")), URI.escape(value.to_s, Regexp.new("[^#{URI::PATTERN::UNRESERVED}]"))].join('=')
#end.join('&')

## Generate the string to be signed
#string_to_sign = "GET\n#{ENDPOINT}\n#{REQUEST_URI}\n#{canonical_query_string}"

## Generate the signature required by the Product Advertising API
#signature = Base64.encode64(OpenSSL::HMAC.digest(OpenSSL::Digest.new('sha256'), AWS_SECRET_KEY, string_to_sign)).strip()

## Generate the signed URL
#request_url = "http://#{ENDPOINT}#{REQUEST_URI}?#{canonical_query_string}&Signature=#{URI.escape(signature, Regexp.new("[^#{URI::PATTERN::UNRESERVED}]"))}"

#puts "Signed URL: \"#{request_url}\""


def scrape_fragrantica_search_product(product):
    global driver

    perfumes = {}
    designers = {}
    driver.get("http://www.fragrantica.com/")
    qajax = driver.find_element_by_id("qajax")
    qajax.clear()
    qajax.send_keys(product)
    time.sleep(3)
    presultsajax = driver.find_element_by_id("presultsajax")
    perfume_a_tags = presultsajax.find_elements_by_tag_name("a")
    for perfume_a_tag in perfume_a_tags:
        pname = perfume_a_tag.text
        purl = perfume_a_tag.get_attribute('href')
        perfumes[pname] = purl
    dresultsajax = driver.find_element_by_id("dresultsajax")
    designer_a_tags = dresultsajax.find_elements_by_tag_name("a")
    for designer_a_tag in designer_a_tags:
        dname = designer_a_tag.text
        durl = designer_a_tag.get_attribute('href')
        designers[dname] = durl
    return perfumes, designers

def scrape_fragrantica_product(product, purl, scrape_choices):
    global driver

    accords = {}
    votes = {}
    notes = {}
    longevity = []
    sillage = []
    also_likes = []
    reviews = []
    reminds_me_of = []

# <div id="prettyPhotoGallery">
#   <div>
#       <div> <span> Main Accords </span></div>
#       <div> <span> Accord </span> <div style="width": 99px></div> </div>
#       <div style="clear: both;"> </div>

    try:
        driver.get(purl)
        msg = "scraping page %s" % (purl)
        print (msg)
        models.scrape_q.put(msg)
    except:
        msg = "page could not be scraped %s" % (purl)
        print (msg)
        models.scrape_q.put(msg)
        return

    # Image
    try:
        mainpicbox = driver.find_element_by_id("mainpicbox")    
        img_tag = mainpicbox.find_element_by_tag_name("img")
        #img_src = 'src=' + img_tag.get_attribute('src')
        img_src = img_tag.get_attribute('src')
    except:
        img_src = ''
        pass

    if 'accords' in scrape_choices:
        try:
            prettyPhotoGallery = driver.find_element_by_id("prettyPhotoGallery")    
            accord_div_tags = prettyPhotoGallery.find_element_by_tag_name("div").find_elements_by_tag_name("div")
            accord_span_tags = prettyPhotoGallery.find_element_by_tag_name("div").find_elements_by_tag_name("span")
            if len(accord_span_tags) > 0:
                for i in range(1, len(accord_span_tags)):
                    accord_span_tag = accord_span_tags[i]
                    accord_div_tag = accord_div_tags[i*3-1]
                    aname = accord_span_tag.text
                    width = accord_div_tag.size['width']
                    width2 = accord_div_tag.get_attribute('style').split(';')[0].split(':')[1]
                    accords[aname] = width
        except:
            pass
    if len(accords) == 0:
        accords['NONE'] = 1

    if 'moods' in scrape_choices:
        try:
            statusDivs_tag = driver.find_element_by_id("statusDivs")
            vote_div_tags = statusDivs_tag.find_elements_by_class_name("votecaption")
            diagramresult_tag = driver.find_element_by_id("diagramresult")
            result_div_tags = diagramresult_tag.find_elements_by_tag_name("div")
            for i in range(0, len(vote_div_tags)):
                vname = vote_div_tags[i].text
                height = result_div_tags[i].size['height']
                votes[vname] = height

     #       votes['total'] = int(driver.find_element_by_id("peopleD").text)
     #       votes['rating avg'] = float(driver.find_element_by_xpath("//span[@itemprop='ratingValue']").text)
     #       votes['rating best'] = float(driver.find_element_by_xpath("//span[@itemprop='bestRating']").text)
        except:
            pass
    if len(votes) == 0:
        votes['NONE'] = 1

    if 'notes' in scrape_choices:
        try:
            userMainNotes_tag = driver.find_element_by_id("userMainNotes")
            note_img_tags = userMainNotes_tag.find_elements_by_tag_name("img")
            note_span_tags = userMainNotes_tag.find_elements_by_tag_name("span")
            total_note_votes = 0
            for i in range(0, len(note_img_tags)):
                nname = note_img_tags[i].get_attribute('title')
                note_votes = int(note_span_tags[i].text)
                notes[nname] = note_votes
                total_note_votes = total_note_votes + note_votes
    #        notes['total'] = total_note_votes
        except:
            pass
    if len(notes) == 0:
        notes['NONE'] = 1

    if 'reviews' in scrape_choices:
        try:
            revND_tags = driver.find_elements_by_class_name("revND")
            dateND_tags = driver.find_elements_by_class_name("dateND")
            for i in range(0, len(revND_tags)):
                review = revND_tags[i].text
                date = dateND_tags[i].get_attribute('textContent').rstrip()
                reviews.append([date, review, 'init'])
        except:
            pass

    return [purl, accords, votes, notes, reviews, img_src]


def scrape_ds(site_choices, scrape_choices, brand_field):
    global driver

    scrape_d = {}
    driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe')
    perfumes = {}
    designers = {}
    scrape_clearresults()
    if 'fragrantica' in site_choices:
        perfumes, designers = scrape_fragrantica_search_product(brand_field)
        for perfume, purl in perfumes.items():
            scrape_d[perfume] = scrape_fragrantica_product(perfume, purl, scrape_choices)
    return list(scrape_d.items())


def scrape_clearresults():
    while not models.scrape_q.empty():
        try:
            models.scrape_q.get(False)
        except Empty:
            continue

def scrape_pollresults_api(request):
    try:
        msg = models.scrape_q.get(block=True, timeout=10)
    except queue.Empty:
        msg = "No update, still working..."
    msg_json = json.dumps(msg)
    return HttpResponse(msg_json, content_type='application/json')

def scrape_accords_json():
    accords_df = pd.DataFrame(columns=['perfume', 'accord', 'rank', 'strength'])
    rownr = 0
    for i in range(0, len(models.scrape_li)):
        perfume = models.scrape_li[i][0]
        accords = models.scrape_li[i][1][1]
        rank = 1
        for accord, width in accords.items():
            accords_df.loc[rownr] = [perfume, accord, rank, int(width)]
            rank = rank + 1
            rownr = rownr + 1
    accords_df_json = accords_df.to_json(orient='records')
    return accords_df_json 

def scrape_votes_json():
    votes_df = pd.DataFrame(columns=['perfume', 'vote', 'rank', 'strength'])
    rownr = 0
    for i in range(0, len(models.scrape_li)):
        perfume = models.scrape_li[i][0]
        votes = models.scrape_li[i][1][2]
        rank = 1
        for vote, height in votes.items():
            votes_df.loc[rownr] = [perfume, vote, rank, int(height)]
            rank = rank + 1
            rownr = rownr + 1
    votes_df_json = votes_df.to_json(orient='records')
    return votes_df_json 

def scrape_notes_json():
    notes_df = pd.DataFrame(columns=['perfume', 'note', 'rank', 'strength'])
    rownr = 0
    for i in range(0, len(models.scrape_li)):
        perfume = models.scrape_li[i][0]
        votes = models.scrape_li[i][1][3]
        rank = 1
        for accord, note_votes in votes.items():
            notes_df.loc[rownr] = [perfume, accord, rank, int(note_votes)]
            rank = rank + 1
            rownr = rownr + 1
    notes_df_json = notes_df.to_json(orient='records')
    return notes_df_json   


def scrape_reviews_json():
    reviews_df = pd.DataFrame(columns=['perfume', 'date', 'label'])
    rownr = 0
    for i in range(0, len(models.scrape_li)):
        perfume = models.scrape_li[i][0]
        reviews = models.scrape_li[i][1][4]
        for j in range(0, len(reviews)):
            date = reviews[j][0]
            date = datetime.strptime(date,'%b %d %Y').strftime('%Y/%m/%d')
            reviews_df.loc[rownr] = [perfume, date, reviews[j][2]]
            rownr = rownr + 1
    reviews_df_json = reviews_df.to_json(orient='records')
    return reviews_df_json 
