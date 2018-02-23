from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import collections
import urllib
import requests
from urllib.parse import urlparse
from requests_ntlm import HttpNtlmAuth
import os
from FMI.settings import BASE_DIR
import base64


import app.models as models


def molecules(ipc_field):
    user = "global\\rd_iis_svc"
    pswrd = "Abs0lut5"

    #url = "http://usubstsappv1.global.iff.com:9944/auth/launchjob?$protocol=Protocols/Web%20Services/RESTful/test&ipc_in=98663"
    params = {
        #"$protocol" : "Protocols/Web Services/RESTful/test",
        "$protocol" : "Protocols/Web Services/RESTful/ipc_properties",
        "ipc_in"    : ipc_field,
        }
    url = "http://usubstsappv1.global.iff.com:9944/auth/launchjob"
    r = requests.get(url, auth=(user, pswrd), params=params)
    if r.status_code != 200:
        print("molecules: get request failed for ipc_properties ", r.status_code)
        return
    molecules_json = r.json()

    params = {
        "$protocol" : "Protocols/Web Services/RESTful/ipc_image",
        "ipc_in"    : ipc_field,
        }
    url = "http://usubstsappv1.global.iff.com:9944/auth/launchjob"
    r = requests.get(url, auth=(user, pswrd), params=params)
    if r.status_code != 200:
        print("molecules: get request failed for ipc_image ", r.status_code)
        return

    #imgdata = base64.b64decode(molecules_json['MOLECULE']) 
    #imgdata = molecules_json['MOLECULE'].decode("base64")
    #b64_string = molecules_json['MOLECULE']
    #b64_bytes = b64_string.encode()
    b64_bytes = r.content
    imgdata = base64.decodebytes(b64_bytes)
    imgdata = r.content
    b64_imgdata = base64.b64encode(imgdata)
    molecules_json['ipc_image'] = b64_imgdata
    img_file = os.path.join(BASE_DIR, 'data/' + 'molecule_' + ipc_field + '.png')
    try:
        with open(img_file, 'wb') as f:
            f.write(imgdata)
    except:
        cwd = os.getcwd()
        print("molecules: working dirtory is: ", cwd)

    return molecules_json

