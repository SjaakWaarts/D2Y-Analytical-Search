__version__ = '3.0-dev'

from .mapping import Indexable, ModelIndex, document_from_model, document_from_index, build_mapping, document_field, deep_field_factory, RawString, RawMultiString, DEFAULT_ANALYZER
from .facets import Facet, TermsFacet, NestedFacet, OptionFacet, KeywordFacet, GlobalTermsFacet, YearHistogram, MonthHistogram, DayHistogram, RangeFilter
from .seekerview import SeekerView, Column, elastic_get
from .utils import search, index, delete
from .registry import register, documents, model_documents, app_documents
from .dashboard import answer_value_decode

default_app_config = 'seeker.apps.SeekerConfig'
