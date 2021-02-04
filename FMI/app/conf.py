from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import collections

import seeker
import seeker.models
import elasticsearch_dsl as dsl

import app.models as models
import app.survey as survey
import app.workbook as workbook


# A site consists of tree of menu items pointing to a site item.
# A site item can be a data selecter: 


conf_edit = {
    'chart_type'  :  {
            "conf_type" : "dropdown",
            "descr"     : "Select Chart Type",
            "options"   : [("Bar", "BarChart"), ("Column", "ColumnChart"), ("Combo", "ComboChart"), ("Line", "LineChart"),
                           ("Pie", "PieChart"), ("Radar", "RadarChart"), ("Table", "Table")],
            },
    'chart_title' : {
            "conf_type" : "text",
            "descr"     : "Enter Chart Title",
            },
    'X_facet.field' : {
            "conf_type" : "dropdown",
            "descr"     : "Select X Facet",
            "options"   : [("attributes", "attributes"), ("ideal_benefits","ideal_benefits")],
            },
    'X_facet.label' : {
            "conf_type" : "text",
            "descr"     : "Enter X label",
            },
    }


