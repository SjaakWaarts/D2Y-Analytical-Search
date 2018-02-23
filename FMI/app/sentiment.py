import pandas as pd
import numpy as np
from urllib.request import urlopen
import requests
import json
import time

import app.models as models



    #if 'reviews' in scrape_choices:
    #    try:
    #        revND_tags = driver.find_elements_by_class_name("revND")
    #        dateND_tags = driver.find_elements_by_class_name("dateND")
    #        for i in range(0, len(revND_tags)):
    #            review = revND_tags[i].text
    #            date = dateND_tags[i].get_attribute('textContent').rstrip()
    #            reviews.append([date, review])
    #    except:
    #        pass

    #return accords, votes, notes, reviews


def sentiment(product):

    url = 'http://text-processing.com/api/sentiment/'
    try:
        for perfume in models.scrape_li:
            perfume_b = perfume[0].encode("ascii", 'replace')
            print('sentiment analysing perfume: ', perfume_b)
            for review in perfume[1][4]:
                if review[2] == 'init':
                    review_b = review[1].encode("ascii", 'replace')
                    data={'text':review_b}
                    r = requests.post(url, data)
                    if r.status_code == 200:
                        answer = r.json()
                        review[2] = answer['label']
    except:
        print('sentiment analysing failed')
            
    return 

  

