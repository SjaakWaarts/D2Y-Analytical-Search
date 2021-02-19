import os
import time
from datetime import datetime
from dateutil.parser import parse
import io
import json
import hashlib
import requests
import urllib
import logging
from slugify import slugify
from selenium import webdriver
from PIL import Image
from django.http import HttpRequest
from django.http import HttpResponse, FileResponse
from django.http import HttpResponseRedirect
import app.aws as aws
import app.workbook as workbook
import app.wb_excel as wb_excel
import dhk_app.recipe as recipe
from FMI.settings import BASE_DIR

logger = logging.getLogger(__name__)

global wd
wd = None

#CSS SELECTOR	Example
#Type selector          h1 {  }
#Universal selector     * {  }
#Class selector         .box {  }
#id selector            #unique { }
#Attribute selector     a[title] {  }, a{href="abc"] { }
#Attribute selector     p[class~="special"] (contains value), div[lang^="zh"] (begins with)
#Pseudo-class sels      p:first-child { }, FIRST CHILD OF PARENT !!!
#                       p:nth-child(An+B) (An is group, B is offset in group 2n+1 for odd)
#                       p:nth-child(-n+3) the first three elements
#                       p:nth-of-typeAn+B), works only for tags (not classes)
#Pseudo-element sels    p::first-line { }
#Descendant combinator  article p
#Child combinator       article > p
#Adjacent sibling       combinator	h1 + p
#General sibling        combinator	h1 ~ p
#
#Combinators of CSS selectors
#Grouping               ,
#Descendant             <space>
#Child                  >
#Siblings               ~
#Adjacent sibling       +
#Column                 ||
#
#XPATH SELECTOR
#Expression	Description
# /	                        direct child
# //	                    descendant
# //div                     select by type
# //div[@id='example']      select by id
# //div[@class='example']   select by class
# //input[@name='username'] select by attribute
# //input[@name='login'and @type='submit']
# //input[@id='username']/following-sibling:input[1]
# //div[contains(text(), 'text')]   # contains text

#path ..	Selects the parent of the current node
#path @	Selects attributes
#
#Attributes and Properties of an element
#.get_property(elm, name)   returns the value of the property with that name
#.get_attribute(elm, name)  first check whether there is a property with that name, otherwise returns attribute with that name
#

def check_categorie_culy(elm):
    valid = True
    span = elm.find_element_by_css_selector("span.list__meta-category")
    elm_text = span.text
    if span.text == "": # lazy read or not visible
        elm_text = span.get_attribute('textContent').strip()
    if elm_text.lower() != 'recepten':
        valid = False
    return valid

def check_ingredients_parts_eefkooktzo(elm):
    valid = True
    li = elm.find_elements_by_css_selector("li")
    if not li:
        valid = False
    return valid

def check_next_page_leukerecepten(elm):
    valid = True
    elm_text = elm.text
    if elm_text == "": # lazy read or not visible
        elm_text = elm.get_attribute('textContent').strip()
    if elm_text.lower() != 'volgende':
        valid = False
    return valid

def con_categories_culy(elm, elm_text):
    try:
        elm_text = elm.get_attribute('content')
        elm_text = elm_text.split('/')
    except:
        elm_text = ""
    return elm_text

def con_categories_24kitchen(elm, elm_text):
    try:
        content = elm.get_attribute('content')
        categories = elm_text.split(',')
        elm_text = []
        for categorie in categories:
            if categorie.strip() != "":
                elm_text.append(categorie.strip())
    except:
        elm_text = ""
    return elm_text

def con_instruction_lekkerensimpel(elm, elm_text):
    try:
        if 'pinterest' in elm_text.lower():
            elm_text = ''
    except:
        elm_text = ""
    return elm_text

def con_links_lekkerensimpel(elm, elm_text):
    try:
        a = elm.find_elements_by_css_selector('a.category-item__anchor')
        href = a[0].get_attribute('href')
        span = elm.find_elements_by_css_selector('h4.category-item__title')
        anchor = span[0].get_attribute('textContent').strip()
        link = {'anchor' : anchor, 'href' : href}
    except:
        link = {}
    return link

def con_links_leukerecepten(elm, elm_text):
    try:
        a = elm.find_elements_by_css_selector('a.full-link')
        href = a[0].get_attribute('href')
        span = elm.find_elements_by_css_selector('span.stream-card__title')
        anchor = span[0].get_attribute('textContent').strip()
        link = {'anchor' : anchor, 'href' : href}
    except:
        link = {}
    return link

def con_links_24kitchen(elm, elm_text):
    global wd

    try:
        anchor = elm.get_attribute('textContent').strip()
        href = wd.current_url + '/' + elm.get_attribute('value').strip()
        link = {'anchor' : anchor, 'href' : href}
    except:
        link = {}
    return link

def field_parser_type(field_parser):
    field_type_split = field_parser['type'].split(':')
    field_type = field_type_split[0]
    if len(field_type_split) == 2:
        field_modifier = field_type_split[1]
    else:
        field_modifier = None
    return field_type, field_modifier

parser_sites_recipe = {
"culy.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["h1.article__title"]},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:published_time']"]},
    'author'        : {'type': 'text', 'con' : "culy.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[property='og:description']", "h1.article__title"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["meta[name='cXenseParse:Taxonomy']"], 'con' : "=con_categories_culy(elm, elm_text)"},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : ["meta[name='cXenseParse:mhu-article_tag']"]},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']", "article:first-child picture.featured-image__picture"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["main article:first-child"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.article__title"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.ingredients ul", "div.wprm-recipe-ingredients"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li[itemprop='ingredients']", "li.wprm-recipe-ingredient", "li"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': {'type' : 'text', 'sels' : ["span.value"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.measure"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["main .article__content:first-child > h2 ~ p"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."]}
                    }
                }
            }
        }
    },
"eatertainment.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["title"]},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:published_time']"]},
    'author'        : {'type': 'text', 'con' : "eatertainment.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']", "meta[property='og:description']"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["main span.meta-info-el.meta-info-cat"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : ["main span.meta-info-el.meta-info-tag a"]},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.entry-title"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["main article:first-child div.entry-content > div.cooked-recipe-ingredients"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["div.cooked-ingredient"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': {'type' : 'text', 'sels' : ["span.cooked-ing-amount"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.cooked-ing-measurement"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["main article:first-child div.entry-content > div.cooked-recipe-directions div.cooked-dir-content"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."]}
                    }
                }
            }
        }
    },
"eefkooktzo.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["meta[property='og:title']"]},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:published_time']"]},
    'author'        : {'type': 'text', 'con' : "eefkooktzo.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[property='og:description']"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : []},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["meta[property='og:title']"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.wprm-recipe-ingredient-group", "ul#zlrecipe-ingredients-list"],
                'check_elm' : "check_ingredients_parts_eefkooktzo(elm)",
                'properties'    : {
                    'part'          : {'type': 'text', 'sels' : ["div.wprm-recipe-ingredient-group-name"], 'cardinality' : '0-1'},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li.wprm-recipe-ingredient", "li"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': {'type' : 'text', 'sels' : ["span.value"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.measure"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["div.wprm-recipe-instruction-group li.wprm-recipe-instruction", "ol#zlrecipe-instructions-list li"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."]}
                    }
                }
            }
        }
    },
"lekkerensimpel.com" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["h1.hero__title"]},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:modified_time']"]},
    'author'        : {'type': 'text', 'con' : "lekkersimpel.com"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']", "h1.hero__title"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["div.hide-for-small-only span.recipe__meta-title"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.hero__title"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.recipe__necessities", "div.entry__content ul"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': {'type' : 'text', 'sels' : ["span.value"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.measure"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["//div[@class='entry__content']/*[normalize-space()='Bereidingswijze:']/following-sibling::p", "div.entry__content > p:nth-child(n+4)"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."], 'con' : "=con_instruction_lekkerensimpel(elm, elm_text)", 'cardinality' : '0-1'}
                    }
                }
            }
        }
    },
"leukerecepten.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : [".page-content__title"]},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:modified_time']", "meta[itemprop='datePublished']"]},
    'author'        : {'type': 'text', 'con' : "leukerecepten.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["ul.page-content__meta li:nth-child(-n+3)"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : [".page-content__title"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["ul.page-content__ingredients-list"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["label"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': None,
                            'measure': None
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["div.page-content__recipe div.step", "div.page-content__recipe p:nth-child(n+2)"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."], 'cardinality' : '0-1'}
                    }
                }
            }
        }
    },
"24kitchen.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["h1.p-name"]},
    'published_date': {'type': 'date', 'sels' : []},
    'author'        : {'type': 'text', 'con' : "24kitchen.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[property='og:description']"]},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["meta[name='keywords'], div.tags li"], 'con' : "=con_categories_24kitchen(elm, elm_text)"},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["."]},
            },
        },
    'cooking_clubs' : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'reviews'       : {
        'type'       : 'nested',
        'properties' : {
            'review'    : None,
            }
        },
    'nutrition'     : None,
    'cooking_times' : None,
    'courses'       : {
        'type'       : 'nested',
        'sels'       : ["/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.p-name"]},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.paragraph--recipe-ingredients-list"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["h3"], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li.recipe-ingredient"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["."]},
                            'value': None,
                            'measure': None
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["section.preparation p > span", "section.preparation p", "section.preparation li"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["."], 'cardinality' : '0-1'}
                    }
                }
            }
        }
    }
}

parser_sites = {
    "culy.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["a.button--secondary.list__button"]},
           'pages'  : ["https://www.culy.nl/recepten/"]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.brand-block__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["main a.list__link"], 'check_elm' : "check_categorie_culy(elm)"},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : ["https://www.culy.nl/recepten/menugang/dessert/"]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["culy.nl"],
           'pages'  : [
               "https://www.culy.nl/recepten/crepes-met-salted-caramel/",
               "https://www.culy.nl/recepten/bomboloni-pistache-witte-chocolade/",
               "https://www.culy.nl/recepten/ijssandwich-met-speculaas/",
               "https://www.culy.nl/recepten/bhurta-met-vissticks-nigella/",
               "https://www.culy.nl/inspiratie/makkelijke-toetjes/",
               ]
           }
        },
    "eatertainment.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["ul.sub-menu.mega-tree li.menu-item-object-category a"]},
           'pages'  : ["https://eatertainment.nl/recepten/"]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.category-title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["h3.entry-title a"]},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : ["https://eatertainment.nl/category/recepten/hoofdgerechten/"]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["eatertainment.nl"],
           'pages'  : [
               "https://eatertainment.nl/garnalen-loempias-uit-de-oven/",
               "https://eatertainment.nl/romige-kerriesoep-met-kalkoen-en-appel/"
               ]
           }
        },
    "eefkooktzo.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["div.site-content a.elementor-button-link"]},
           'pages'  : ["https://www.culy.nl/recepten/"]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.elementor-heading-title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["a.uael-post__read-more"]},
           'next_page' : {'type:href': 'text', 'sels' : ["a.next.page-numbers"]},
           'pages'  : ["https://www.eefkooktzo.nl/category/ovenschotels-stamppotjes/"]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["eefkooktzo.nl"],
           'pages'  : [
               "https://www.eefkooktzo.nl/visovenschotel/",
               "https://www.eefkooktzo.nl/makkelijke-moussaka/",
               "https://www.eefkooktzo.nl/zuurkool-ovenschotel-met-spekjes-en-appel/"
               ]
           }
        },
    "lekkerensimpel.com" : {
        'index_page' : {
            'links'    : {'type': 'links', 'sels' : ["div.category-item"], 'con' : "=con_links_lekkerensimpel(elm, elm_text)"},
            'pages'     : ["https://www.lekkerensimpel.com/recepten/"]
            },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.hero__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["a.post-item__anchor"]},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : ["https://www.lekkerensimpel.com/lunchrecepten/"]
           },
        'recipe_page' : {
            'parser'    : parser_sites_recipe["lekkerensimpel.com"],
            'pages' : [
                "https://www.lekkerensimpel.com/mexicaans-broodje-kip/",
                "https://www.lekkerensimpel.com/pasta-pesto-met-spinazie-en-zalm/",
                ]
            }
        },
    "leukerecepten.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["div.stream-card"], 'con' : "=con_links_leukerecepten(elm, elm_text)"},
           'pages'  : ["https://www.leukerecepten.nl/recepten-index/"]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.page__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["div.rhythm-s a.full-link"]},
           'next_page' : {'type': 'text:href', 'sels' : ["ul.pagination li:last-child a"], 'check_elm' : "check_next_page_leukerecepten(elm)"},
           'pages'  : ["https://www.leukerecepten.nl/ovenschotels/"]
           },
        'recipe_page' : {
            'parser'    : parser_sites_recipe["leukerecepten.nl"],
            'pages' : ["https://www.leukerecepten.nl/recepten/lasagne-paprika/"]
            }
        },
    "24kitchen.nl" : {
        'index_page' : {
           'links' : {'type': 'links',
                      'sels' : ["select[name='soort_gerecht'] option, select[name='menugang'] option, select[name='keuken'] option"],
                      'con' : "=con_links_24kitchen(elm, elm_text)"},
           'pages'  : ["https://www.24kitchen.nl/recepten"]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["div.search-filter-select.active"]},
           'links' : {'type': 'text-array:href', 'sels' : ["div.search-content a.full-click-link"]},
           'next_page' : {'scroll' : True},
           'pages'  : [
               "https://www.24kitchen.nl/recepten/zoeken/soort_gerecht/ovenschotel-101",
               ]
           },
        'recipe_page' : {
            'parser' : parser_sites_recipe["24kitchen.nl"],
            'pages'  : [
                "https://www.24kitchen.nl/recepten/kastanjesoep-met-salieroom-en-crouton-sterren",
                "https://www.24kitchen.nl/recepten/wortelovenschotel",
                "https://www.24kitchen.nl/recepten/gevulde-pasta-met-pesto-en-spinazie",
                ]
            },
        },
    }

def webdriver_start():
    global wd

    if wd is None:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument("--headless")
        wd = webdriver.Chrome(options=options)
    return wd

def webdriver_get(page):
    global wd
    WAIT_TIME = 2
    
    wd.get(page)
    # wait for the element to load
    try:
        webdriver.support.ui.WebDriverWait(wd, WAIT_TIME).until(lambda s: s.find_element_by_tag_name("body").is_displayed())
        return wd
    except TimeoutException:
        print("TimeoutException: Element not found")
        return None

def webdriver_scroll(page):
    global wd
    WAIT_TIME = 2
    SCROLL_PAUSE_TIME = 0.5
    
    wd.get(page)
    # wait for the element to load
    try:
        webdriver.support.ui.WebDriverWait(wd, WAIT_TIME).until(lambda s: s.find_element_by_tag_name("body").is_displayed())
    except TimeoutException:
        print("TimeoutException: Element not found")
        return None

    # Get scroll height
    last_height = wd.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        # Calculate new scroll height and compare with last scroll height
        new_height = wd.execute_script("return document.body.scrollHeight")
        logger.info(f"Scroll '{page}' from heights {last_height} to {new_height}")
        if new_height == last_height:
            break
        last_height = new_height

def webdriver_stop():
    global wd

    wd.close()
    wd.quit()


def carousel_scrape(query: str, max_links_to_fetch: int, sleep_between_interactions: float = 0.1):
    global wd

    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    wd = webdriver_start()
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"
    wd.get(search_url.format(q=query))
    thumbnails = []
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)
        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            ## try to click every thumbnail such that we can get the real image behind it
            #try:
            #    img.click()
            #    time.sleep(sleep_between_interactions)
            #except Exception:
            #    continue

            ## extract image urls
            #actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            #for actual_image in actual_images:
            #    if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
            #        thumbnails.append(actual_image.get_attribute('src'))
            if img.get_attribute('src'):
                thumbnail = {}
                thumbnail['src'] = img.get_attribute('src')
                thumbnail['alt'] = img.get_attribute('alt')
                thumbnail['width'] = img.get_attribute('width')
                thumbnail['height'] = img.get_attribute('height')
                thumbnails.append(thumbnail)
            image_count = len(thumbnails)
            if len(thumbnails) >= max_links_to_fetch:
                print(f"Found: {len(thumbnails)} image links, done!")
                break
        else:
            print("Found:", len(thumbnails),
                  "image links, looking for more ...")
            time.sleep(30)
            return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)
    webdriver_stop()
    return thumbnails

def scrape_init_value(field_type, field_modified=None):
    field_value = ""
    if field_type == 'nested':
        field_value = []
    elif field_type == 'text-array':
        field_value = []
    elif field_type == 'links':
        field_value = []
    elif field_type == 'integer':
        field_value = 0
    elif field_type == 'date':
        field_value = '2019-01-01' # datetime.now().strftime('%Y-%m-%d')
    else:
        field_value = ""
    return field_value

def scrape_links(page, parser_site):
    global wd

    taxonomy = ""
    links = []
    first_page = True
    next_page = True
    pagenr = 0
    while next_page:
        logger.info(f"Scrape links on '{page}'")
        scroll = parser_site.get('next_page', {}).get('scroll', False)
        if scroll:
            webdriver_scroll(page)
        else:
            webdriver_get(page)
        root_elm = wd.find_element_by_tag_name('html')
        if first_page:
            field_parser = parser_site.get('taxonomy', {})
            elms = scrape_elements(root_elm, field_parser)
            if elms:
                taxonomy = scrape_values(elms[0], field_parser, taxonomy)
            first_page = False
        field_parser = parser_site['links']
        elms = scrape_elements(root_elm, field_parser)
        for elm in elms:
            links = scrape_values(elm, field_parser, links)
        field_parser = parser_site.get('next_page', {})
        elms = scrape_elements(root_elm, field_parser)
        if elms:
            page = elms[0].get_attribute('href')
            pagenr = pagenr + 1
            if pagenr > 2:
                next_page = False
        else:
            next_page = False

    return (taxonomy, links)

def scrape_elements(root_elm, field_parser, mode="cor"):
    sels = field_parser.get('sels', [])
    child_elms = []
    scrape_sel = None # the selector that returns elements
    if len(sels) == 0:
        return []
    if mode == "cor":
        for sel in sels:
            if sel[0] == '/' or sel in ['.', '..']:
                elms = root_elm.find_elements_by_xpath(sel)
            else:
                elms = root_elm.find_elements_by_css_selector(sel)
            for elm in elms:
                if 'check_elm' in field_parser:
                    valid = eval(field_parser['check_elm'])
                else:
                    valid = True
                if valid:
                    child_elms.append(elm)
            if len(elms) > 0:
                scrape_sel = sel
                break
    else:
        stack = [(root_elm, 0)]
        while len(stack):
            node = stack.pop()
            root_elm = node[0]
            sel = sels[node[1]]
            if sel[0] == '/' or sel in ['.', '..']:
                elms = root_elm.find_elements_by_xpath(sel)
            else:
                elms = root_elm.find_elements_by_css_selector(sel)
            for elm in elms:
                if node[1] == len(sels) - 1:
                    child_elms.append(elm)
                    scrape_sel = sel
                else:
                    stack.append((elm, node[1] + 1))
    return child_elms

def scrape_values(elm, field_parser, field_value):
    field_type, field_modifier = field_parser_type(field_parser)
    # 1. First get text
    elm_text = elm.text
    if elm.text == "": # lazy read or not visible
        elm_text = elm.get_attribute('textContent').strip()
    if elm.tag_name == 'meta':
        elm_text = elm.get_attribute('content')
    elif elm.tag_name == 'a':
        href = elm.get_attribute('href')
        if field_type == 'links':
            elm_text = {'achor' : elm_text, 'href' : href}
        else:
            if field_modifier == 'href':
                elm_text = href
    # 2. Check on construtur to obtain text or format text, contstrucor has elm and elm_text as input
    if 'con' in field_parser:
        con = field_parser['con']
        if con[0] == '=':
            if con[1] == '.':
                elm_text = eval('elm' + con[1:])
            else:
                elm_text = eval(con[1:])
        else:
            elm_text = con
    # 3. default again to text
    if elm_text is None:
        elm_text = elm.text
        if elm.text == "": # lazy read or not visible
            elm_text = elm.get_attribute('textContent').strip()
    if field_type == 'nested':
        if len(elm_text) > 0:
            field_value.append(elm_text)
    elif field_type == 'text-array':
        if len(elm_text) > 0:
            if type(elm_text) == list:
                field_value.extend(elm_text)
            else:
                if elm_text not in field_value:
                    field_value.append(elm_text)
    elif field_type == 'links':
        if len(elm_text) > 0:
            if 'con' in field_parser:
                link = elm_text
            else:
                link = {'anchor': elm.get_attribute('textContent').strip(), 'href' : elm.get_attribute('href')}
            field_value.append(link)
    elif field_type == 'integer':
        try:
            field_value = int(elm_text)
        except:
            field_value = 0
    elif field_type == 'date':
        field_value = parse(elm_text).strftime('%Y-%m-%d')
    else:
        field_value = field_value + elm_text
    return field_value


def scrape_recipe(root_elm, parser_recipe, path = ""):
    global wd

    recipe = {}
    errors = []
    for field_name, field_parser in parser_recipe.items():
        if field_parser is None:
            continue
        if field_parser.get('sels', None) is None and field_parser.get('con', None) is not None:
            recipe[field_name] = field_parser['con']
            continue
        field_name_full = field_name if not path else path + '.' + field_name
        field_type, field_modifier = field_parser_type(field_parser)
        field_value = scrape_init_value(field_type)
        sels = field_parser.get('sels', [])
        elms = scrape_elements(root_elm, field_parser)
        if field_type == 'nested':
            for elm in elms:
                elm_value, nested_errors = scrape_recipe(elm, field_parser['properties'], field_name_full)
                for k, v in elm_value.items():
                    # check there is a value, or 0 in case of an integer
                    if v or v == 0:
                        field_value.append(elm_value)
                        break
                if len(nested_errors):
                    errors.extend(nested_errors)
        else:
            for elm in elms:
                field_value = scrape_values(elm, field_parser, field_value)
        if len(sels) > 0 and len(elms) == 0:
            cardinality = field_parser.get('cardinality', "1")
            if cardinality[0] == '1':
                errors.append({field_name : f"Element not found for selector {sels}"})
        recipe[field_name] = field_value
    return recipe, errors

def recipe_scrape(request):
    global wd

    page_type = request.GET['page_type']
    page = request.GET['page']
    mode = request.GET['mode']

    logger.info(f"Scrape request for '{page_type}', '{page}'")
    recipe_scrape_results = []

    site = urllib.parse.urlparse(page).netloc.split(':')[0]
    domain = '.'.join(site.split('.')[-2:])
    if domain not in parser_sites:
        return None
    parser_site = parser_sites[domain]
    webdriver_start()

    if page_type == 'index_page':
        categorie_links = scrape_links(page, parser_site['index_page'])[1]
        page_type = 'categorie_page'
    else:
        categorie_links = [{'anchor' : '', 'href' : page}]

    if mode == 'taxanomy':
        for categorie_link in categorie_links:
            recipe_scrape_results.append(('#', categorie_link['anchor'], categorie_link['href'], []))
        dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'scrape')
        filename_full = os.path.join(dirname, domain + '.json')
        with open(filename_full, 'w') as fp:
            json.dump(recipe_scrape_results, fp, indent=4, separators= (',', ': '))

    if mode == 'scrape':
        if page_type == 'categorie_page':
            taxonomy_links = []
            for categorie_link in categorie_links:
                categorie_page = categorie_link['href']
                logger.info(f"Scrape categorie page '{categorie_page}'")
                taxonomy_links.append(scrape_links(categorie_page, parser_site['categorie_page']))
            page_type = 'recipe_page'
        else:
            taxonomy_links = [(None, [page])]

        for taxonomy_link in taxonomy_links:
            taxonomy = taxonomy_link[0]
            recipe_links = taxonomy_link[1]
            for recipe_page in recipe_links:
                logger.info(f"Scrape recipe page '{recipe_page}'")
                webdriver_get(recipe_page)
                root_elm = wd.find_element_by_tag_name('html')
                recipe_new, errors = scrape_recipe(root_elm, parser_site['recipe_page']['parser'])
                if len(errors) == 0:
                    id = slugify(recipe_page)
                    recipe_new['id'] = recipe_page
                    if taxonomy and taxonomy not in recipe_new['categories']:
                        recipe_new['categories'].append(taxonomy)
                    recipe_obj = recipe.Recipe(id, recipe=recipe_new)
                    recipe_obj.screen()
                    resp = recipe_obj.put()
                    if not resp.ok:
                        errors.append({'ES put failed' : resp.text})
                else:
                    id = '#'
                recipe_scrape_results.append((id, recipe_new['title'], recipe_page, errors))

    # leave the driver running
    # webdriver_stop()
    context = {
        'recipe_scrape_results'  : recipe_scrape_results,
        }
    return HttpResponse(json.dumps(context), content_type='application/json')
