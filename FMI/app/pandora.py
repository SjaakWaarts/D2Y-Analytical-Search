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
import app.workbooks as workbooks


# Pandora is the Sensory Data Analysis used by Flavors. It is an R package.
#
# Panel Performance or Descriptive Analysis
# - MDP/QDA Summary
# - MDP/QDA Long Term
# - Consensus Profiling
# - Free Sorting (Summary)
#
# https://www.sensorysociety.org/knowledge/sspwiki/Pages/Title-List.aspx
# QDA   Quantitative Descriptive Analysis
# 

