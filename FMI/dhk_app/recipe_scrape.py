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


taxonomy = {
    "Avond" : [
        "Bijgerecht",
	    "Borrelhapje",
	    "Dessert",
	    "Diner",
	    "Dressings",
	    "Hoofdgerecht",
	    "Menu",
	    "Salades",
	    "Sauzen",
	    "Smoothies",
	    "Snacks",
	    "Soep",
	    "Soepen",
	    "Tussendoor",
	    "Voorgerecht",
	    "Zoet"],
    "Bakken" : [
        "Cake",
	    "Cheesecake",
	    "Koekjes",
	    "Muffin",
	    "Taart",
	    "Wafel"],
    "Bereiding" : [
        "Bakken",
	    "BBQ",
	    "Gourmet"],
    "Dieet" : [
        "Gezond",
	    "Glutenvrij",
	    "Koolhydraatarm",
	    "Vegan",
	    "Vegetarisch"],
    "Hoofdgerecht" : [
        "Aardappel",
	    "Aardappelen",
	    "Bladerdeeg",
	    "Bruschettas",
	    "Dips ",
	    "Eieren",
	    "Gehakt",
	    "Groente",
	    "Hartigetaart",
	    "Kip",
	    "Lasagna",
	    "Ovenschotel",
	    "Pasta",
	    "Pizza",
	    "Quiche",
	    "Rijst",
	    "Stampot",
	    "Stamppot",
	    "Vis",
	    "Vlees"],
    "Land" : [
        "Amerikaans",
	    "Arabisch",
	    "Australisch",
	    "Aziatisch",
	    "Belgisch",
	    "Engels",
	    "Frans",
	    "Grieks",
	    "Hollands",
	    "Indisch",
	    "Italiaans",
	    "Marokkaans",
	    "Mediterraans",
	    "Mexicaans",
	    "Nederlands",
	    "Oost-Europees",
	    "Scandinavisch",
	    "Spaans",
	    "Turks",
	    "Zuid-Afrikaans",
	    "Zuid-Amerikaans"],
    "Overdag" :  [
        "Brood",
	    "Lunch",
	    "Ontbijt",
	    "Tussendoor",
	    "Wraps"],
    "Seizoen" :  [
        "Herfst",
	    "Lente",
	    "Winter",
	    "Zomer"],
    "Speciaal" : [
        "Camping",
	    "Familie",
	    "Gezond",
	    "High-tea",
	    "Kerst",
	    "Kinderen",
	    "Oranje",
	    "Oud-en-nieuw",
	    "Pasen",
	    "Sinterklaas",
	    "Snel",
	    "Tapas",
	    "Thema",
	    "Valentijn"],
}

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
           'links' : {'type': 'links', 'sels' : ["a.button--primary, a.button--secondary"]},
           'pages'  : [
               "All Categories",
              "https://www.culy.nl/recepten/"
              ]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.brand-block__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["main a.list__link"], 'check_elm' : "check_categorie_culy(elm)"},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : [
                ("Menu", "https://www.culy.nl/recepten/menugang/"),
                ("Pasen", "https://www.culy.nl/tag/paasbrunch"),
                ("Ontbijt", "https://www.culy.nl/recepten/menugang/ontbijt/"),
                ("Lunch", "https://www.culy.nl/recepten/menugang/lunch/"),
                ("Diner", "https://www.culy.nl/recepten/menugang/diner/"),
                ("Dessert", "https://www.culy.nl/recepten/menugang/dessert/"),
                ("Snacks", "https://www.culy.nl/recepten/menugang/snack/"),
                ("Snel", "https://www.culy.nl/tag/snelle-recepten/"),
                ("Snel", "https://www.culy.nl/tag/makkelijke-recepten/"),
                ("Vegetarisch", "https://www.culy.nl/vegetarisch/"),
                ("Kinderen", "https://www.culy.nl/tag/culy-kids/"),
                ("Gezond", "https://www.culy.nl/tag/gezonde-recepten/"),
                ("Italiaans", "https://www.culy.nl/tag/italiaans"),
                ("Mexicaans", "https://www.culy.nl/tag/mexicaans/"),
                ("Marokkaans", "https://www.culy.nl/tag/marokkaans/"),
                ("Turks", "https://www.culy.nl/tag/turks/"),
                ("Grieks", "https://www.culy.nl/tag/grieks/"),
                ("Ovenschotel", "https://www.culy.nl/tag/ovengerechten/"),
               ]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["culy.nl"],
           'pages'  : [
               ("Dessert", "https://www.culy.nl/recepten/crepes-met-salted-caramel/"),
               ("Dessert", "https://www.culy.nl/recepten/bomboloni-pistache-witte-chocolade/"),
               ("Dessert", "https://www.culy.nl/recepten/ijssandwich-met-speculaas/"),
               ("Vis", "https://www.culy.nl/recepten/bhurta-met-vissticks-nigella/"),
               ("Dessert", "https://www.culy.nl/inspiratie/makkelijke-toetjes/"),
               ]
           }
        },
    "eatertainment.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["div.navbar-outer ul.main-menu li:first-child div.mega-holder ul.sub-menu.mega-tree li.menu-item a"]},
           'pages'  : [
               "All Categories",
               "https://eatertainment.nl/recepten/"
               ]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.category-title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["h3.entry-title a"]},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : [
                ("Ontbijt", "https://eatertainment.nl/category/recepten/ontbijt/"),
                ("Lunch", "https://eatertainment.nl/category/recepten/lunch-brunch/"),
                ("Voorgerecht", "https://eatertainment.nl/category/recepten/voorgerecht/"),
                ("Hoofdgerecht", "https://eatertainment.nl/category/recepten/hoofdgerechten/"),
                ("Dessert", "https://eatertainment.nl/category/recepten/desserts/"),
                ("Tussendoor", "https://eatertainment.nl/category/recepten/tussendoortjes/"),
                ("Borrelhapje", "https://eatertainment.nl/category/recepten/borrel/"),
                ("Thema", "https://eatertainment.nl/category/thema/"),
               ]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["eatertainment.nl"],
           'pages'  : [
               ("Hoofdgerecht", "https://eatertainment.nl/garnalen-loempias-uit-de-oven/"),
               ("Hoofdgerecht", "https://eatertainment.nl/romige-kerriesoep-met-kalkoen-en-appel/")
               ]
           }
        },
    "eefkooktzo.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["div.site-content a.elementor-button-link"]},
           'pages'  : [
               "All Categories",
               "https://www.eefkooktzo.nl/recepten-index/"
               ]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.elementor-heading-title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["a.uael-post__read-more"]},
           'next_page' : {'type:href': 'text', 'sels' : ["a.next.page-numbers"]},
           'pages'  : [
                ("Snel", "https://www.eefkooktzo.nl/tag/30-minuten-of-minder/"),
                ("BBQ", "https://www.eefkooktzo.nl/tag/bbq/"),
                ("Bijgerecht", "https://www.eefkooktzo.nl/tag/bijgerechten/"),
                ("Borrelhapje", "https://www.eefkooktzo.nl/tag/voor-bij-de-borrel/"),
                ("Pasta", "https://www.eefkooktzo.nl/category/deegwaren-brood-pizza/"),
                ("Snel", "https://www.eefkooktzo.nl/tag/easy-peasy-friday/"),
                ("Hartigetaart", "https://www.eefkooktzo.nl/category/hoofdgerechten/hartige-taarten-quiches/"),
                ("Dessert", "https://www.eefkooktzo.nl/category/toetjes/ijs/"),
                ("Kip", "https://www.eefkooktzo.nl/category/hoofdgerechten/kip-gevogelte/"),
                ("", "https://www.eefkooktzo.nl/category/kruidenmixen/"),
                ("Lunch", "https://www.eefkooktzo.nl/tag/lunch/"),
                ("Ovenschotel", "https://www.eefkooktzo.nl/category/ovenschotels-stamppotjes/"),
                ("Ontbijt", "https://www.eefkooktzo.nl/category/ontbijt/"),
                ("Italiaans", "https://www.eefkooktzo.nl/category/pasta-italiaanse-gerechten/"),
                ("Salades", "https://www.eefkooktzo.nl/category/salade/"),
                ("Sauzen", "https://www.eefkooktzo.nl/category/saus-smeerseltjes-dips-dressing/"),
                #("", "https://www.eefkooktzo.nl/tag/slowcooker/"),
                ("Soep", "https://www.eefkooktzo.nl/category/soep/"),
                ("Dessert", "https://www.eefkooktzo.nl/category/toetjes/"),
                ("Tussendoor", "https://www.eefkooktzo.nl/tag/tussendoortjes/"),
                ("Vegan", "https://www.eefkooktzo.nl/category/hoofdgerechten/vega/"),
                ("Vis", "https://www.eefkooktzo.nl/category/hoofdgerechten/vis-schaal-schelpdieren/"),
                ("Vlees", "https://www.eefkooktzo.nl/category/hoofdgerechten/vlees/"),
                ("Voorgerecht", "https://www.eefkooktzo.nl/category/voorgerechten/"),
                ("Taart", "https://www.eefkooktzo.nl/category/zoete-baksels/"),
                ("Kerst", "https://www.eefkooktzo.nl/tag/kerst/"),
                ("Sinterklaas", "https://www.eefkooktzo.nl/tag/sinterklaas/"),
                ("Pasen", "https://www.eefkooktzo.nl/tag/pasen/"),
               ]
           },
        'recipe_page' : {
           'parser' : parser_sites_recipe["eefkooktzo.nl"],
           'pages'  : [
               ("Vis", "https://www.eefkooktzo.nl/visovenschotel/"),
               ("Ovenschotel", "https://www.eefkooktzo.nl/makkelijke-moussaka/"),
               ("Ovenschotel", "https://www.eefkooktzo.nl/zuurkool-ovenschotel-met-spekjes-en-appel/"),
               ]
           }
        },
    "lekkerensimpel.com" : {
        'index_page' : {
            'links'    : {'type': 'links', 'sels' : ["div.category-item"], 'con' : "=con_links_lekkerensimpel(elm, elm_text)"},
            'pages'     : [
               "All Categories",
                "https://www.lekkerensimpel.com/recepten/"
                ]
            },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.hero__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["a.post-item__anchor"]},
           'next_page' : {'type': 'text:href', 'sels' : ["a.next.page-numbers"]},
           'pages'  : [
                ("Ontbijt", "https://www.lekkerensimpel.com/ontbijtrecepten/"),
                ("Lunch", "https://www.lekkerensimpel.com/lunchrecepten/"),
                ("Tussendoor", "https://www.lekkerensimpel.com/tussendoortjes/"),
                ("Hoofdgerecht", "https://www.lekkerensimpel.com/hoofdgerechten/"),
                ("Bijgerecht", "https://www.lekkerensimpel.com/bijgerechten/"),
                ("Dessert", "https://www.lekkerensimpel.com/nagerechten/"),
                ("Salades", "https://www.lekkerensimpel.com/salades/"),
                ("Soep", "https://www.lekkerensimpel.com/hoofdgerechten/soep/"),
                ("Bakken", "https://www.lekkerensimpel.com/bakken/"),
                ("Dressings", "https://www.lekkerensimpel.com/salades/dressings/"),
                ("Sauzen", "https://www.lekkerensimpel.com/sauzen/"),
                ("Snel", "https://www.lekkerensimpel.com/snelle-recepten/"),
                ("Tapas", "https://www.lekkerensimpel.com/tapas-recepten/"),
                ("BBQ", "https://www.lekkerensimpel.com/barbecue-recepten/"),
                ("High-tea", "https://www.lekkerensimpel.com/high-tea-recepten/"),
                ("Kinderen", "https://www.lekkerensimpel.com/kinderrecepten/"),
                ("Familie", "https://www.lekkerensimpel.com/familie-recepten/"),
                ("Camping", "https://www.lekkerensimpel.com/campingrecepten/"),
                ("Stampot", "https://www.lekkerensimpel.com/tag/stamppot/"),
                ("Ovenschotel", "https://www.lekkerensimpel.com/hoofdgerechten/ovenschotels/"),
                ("Hartigetaart", "https://www.lekkerensimpel.com/tag/hartige-taart/"),
                ("Zoet", "https://www.lekkerensimpel.com/tag/zoet/"),
                ("Herfst", "https://www.lekkerensimpel.com/herfst-recepten/"),
                ("Winter", "https://www.lekkerensimpel.com/winter-recepten/"),
                ("Lente", "https://www.lekkerensimpel.com/lente-recepten/"),
                ("Zomer", "https://www.lekkerensimpel.com/zomer-recepten/"),
                ("Italiaans", "https://www.lekkerensimpel.com/italiaanse-recepten/"),
                ("Grieks", "https://www.lekkerensimpel.com/griekse-recepten/"),
                ("Mexicaans", "https://www.lekkerensimpel.com/mexicaanse-recepten/"),
                ("Amerikaans", "https://www.lekkerensimpel.com/amerikaanse-recepten/"),
                ("Aziatisch", "https://www.lekkerensimpel.com/oosterse-recepten/"),
                ("Hollands", "https://www.lekkerensimpel.com/hollandse-recepten/"),
                ("Sinterklaas", "https://www.lekkerensimpel.com/sinterklaas-recepten/"),
                ("Kerst", "https://www.lekkerensimpel.com/kerstrecepten/"),
                ("Oud-en-nieuw", "https://www.lekkerensimpel.com/oud-en-nieuw/"),
                ("Pasen", "https://www.lekkerensimpel.com/paasrecepten/"),
                ("Oranje", "https://www.lekkerensimpel.com/oranje-recepten/"),
                ("Kip", "https://www.lekkerensimpel.com/tag/kip/"),
                ("Gehakt", "https://www.lekkerensimpel.com/tag/gehakt/"),
                ("Vlees", "https://www.lekkerensimpel.com/hoofdgerechten/vlees/"),
                ("Vis", "https://www.lekkerensimpel.com/hoofdgerechten/vis/"),
                ("Aardappel", "https://www.lekkerensimpel.com/tag/aardappel/"),
                ("Wraps", "https://www.lekkerensimpel.com/tag/wraps/"),
                ("Brood", "https://www.lekkerensimpel.com/tag/brood/"),
                ("Pasta", "https://www.lekkerensimpel.com/hoofdgerechten/pasta/"),
                ("Rijst", "https://www.lekkerensimpel.com/hoofdgerechten/rijst/"),
                ("Vegetarisch", "https://www.lekkerensimpel.com/hoofdgerechten/vegetarisch-recepten/"),
                ("Vegan", "https://www.lekkerensimpel.com/vegan-recepten/"),
                ("Koolhydraatarm", "https://www.lekkerensimpel.com/koolhydraatarme-recepten/"),
               ]
           },
        'recipe_page' : {
            'parser'    : parser_sites_recipe["lekkerensimpel.com"],
            'pages' : [
                ("Lunch", "https://www.lekkerensimpel.com/mexicaans-broodje-kip/"),
                ("Hoofdgerecht", "https://www.lekkerensimpel.com/pasta-pesto-met-spinazie-en-zalm/"),
                ]
            }
        },
    "leukerecepten.nl" : {
        'index_page' : {
           'links' : {'type': 'links', 'sels' : ["div.stream-card"], 'con' : "=con_links_leukerecepten(elm, elm_text)"},
           'pages'  : [
               "All Categories",
               "https://www.leukerecepten.nl/recepten-index/"
               ]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["h1.page__title"]},
           'links' : {'type': 'text-array:href', 'sels' : ["div.rhythm-s a.full-link"]},
           'next_page' : {'type': 'text:href', 'sels' : ["ul.pagination li:last-child a"], 'check_elm' : "check_next_page_leukerecepten(elm)"},
           'pages'  : [
                ("Smoothies", "https://www.leukerecepten.nl/smoothie-recepten/"),
                ("Bruschettas", "https://www.leukerecepten.nl/bruschettas/"),
                ("Stamppot", "https://www.leukerecepten.nl/stamppot-recepten/"),
                ("Quiche", "https://www.leukerecepten.nl/quiche-recepten/"),
                ("Pizza", "https://www.leukerecepten.nl/pizza-recepten/"),
                ("Lasagna", "https://www.leukerecepten.nl/lasagne-recepten/"),
                ("Dips ", "https://www.leukerecepten.nl/spreads-en-dips/"),
                ("Sauzen", "https://www.leukerecepten.nl/sauzen/"),
                ("Snel", "https://www.leukerecepten.nl/020-min/"),
                ("BBQ", "https://www.leukerecepten.nl/barbecue-recepten/"),
                ("Kinderen", "https://www.leukerecepten.nl/kinderrecepten/"),
                ("Snacks", "https://www.leukerecepten.nl/gerechten/hapjes/"),
                ("Ovenschotel", "https://www.leukerecepten.nl/ovenschotels/"),
                ("Bakken", "https://www.leukerecepten.nl/gerechten/bakrecepten/"),
                ("Salades", "https://www.leukerecepten.nl/salades/"),
                ("Soep", "https://www.leukerecepten.nl/soep-recepten/"),
                ("Tapas", "https://www.leukerecepten.nl/tapas-recepten/"),
                ("Gezond", "https://www.leukerecepten.nl/gezonde-recepten/"),
                ("Ontbijt", "https://www.leukerecepten.nl/gerechten/ontbijt/"),
                ("Tussendoor", "https://www.leukerecepten.nl/gerechten/tussendoortjes/"),
                ("Voorgerecht", "https://www.leukerecepten.nl/gerechten/voorgerechten/"),
                ("Hoofdgerecht", "https://www.leukerecepten.nl/gerechten/hoofdgerechten/"),
                ("Bijgerecht", "https://www.leukerecepten.nl/gerechten/bijgerechten/"),
                ("Dessert", "https://www.leukerecepten.nl/gerechten/nagerechten/"),
                ("Lunch", "https://www.leukerecepten.nl/gerechten/lunch/"),
                ("Oud-en-nieuw", "https://www.leukerecepten.nl/oud-en-nieuw-recepten/"),
                ("Valentijn", "https://www.leukerecepten.nl/valentijnsrecepten/"),
                ("Sinterklaas", "https://www.leukerecepten.nl/sinterklaas-recepten/"),
                ("Gourmet", "https://www.leukerecepten.nl/gourmet-recepten/"),
                ("Oranje", "https://www.leukerecepten.nl/oranje-recepten/"),
                ("High-tea", "https://www.leukerecepten.nl/high-tea-recepten/"),
                ("Kerst", "https://www.leukerecepten.nl/kerstrecepten/"),
                ("Pasen", "https://www.leukerecepten.nl/paasrecepten/"),
                ("Koolhydraatarm", "https://www.leukerecepten.nl/dieet/koolhydraatarme-recepten/"),
                ("Glutenvrij", "https://www.leukerecepten.nl/dieet/glutenvrije-recepten/"),
                ("Vegetarisch", "https://www.leukerecepten.nl/vegetarische-recepten/"),
                ("Vegan", "https://www.leukerecepten.nl/vegan-recepten/"),
                ("Lente", "https://www.leukerecepten.nl/lente-recepten/"),
                ("Zomer", "https://www.leukerecepten.nl/zomer-recepten/"),
                ("Herfst", "https://www.leukerecepten.nl/herfstrecepten/"),
                ("Winter", "https://www.leukerecepten.nl/winter-recepten/"),
                ("Taart", "https://www.leukerecepten.nl/taart-recepten/"),
                ("Cake", "https://www.leukerecepten.nl/cake-recepten/"),
                ("Muffin", "https://www.leukerecepten.nl/muffin-recepten/"),
                ("Koekjes", "https://www.leukerecepten.nl/koekjes-recepten/"),
                ("Cheesecake", "https://www.leukerecepten.nl/cheesecake-recepten/"),
                ("Wafel", "https://www.leukerecepten.nl/wafel-recepten/"),
                ("Vlees", "https://www.leukerecepten.nl/vlees-vis/gehakt/"),
                ("Groente", "https://www.leukerecepten.nl/groenten-fruit/paprika/"),
                ("Aardappelen", "https://www.leukerecepten.nl/diverse/aardappelen/"),
                ("Vis", "https://www.leukerecepten.nl/vlees-vis/zalm/"),
                ("Rijst", "https://www.leukerecepten.nl/diverse/rijst/"),
                ("Bladerdeeg", "https://www.leukerecepten.nl/diverse/bladerdeeg/"),
                ("Aardappelen", "https://www.leukerecepten.nl/zoete-aardappel-recepten/"),
                ("Wraps", "https://www.leukerecepten.nl/diverse/wraps/"),
                ("Kip", "https://www.leukerecepten.nl/kip-recepten/"),
                ("Pasta", "https://www.leukerecepten.nl/pasta-recepten/"),
               ]
           },
        'recipe_page' : {
            'parser'    : parser_sites_recipe["leukerecepten.nl"],
            'pages' : [
                ("Hoofdgerecht", "https://www.leukerecepten.nl/recepten/lasagne-paprika/"),
                ]
            }
        },
    "24kitchen.nl" : {
        'index_page' : {
           'links' : {'type': 'links',
                      'sels' : ["select[name='soort_gerecht'] option, select[name='menugang'] option, select[name='keuken'] option"],
                      'con' : "=con_links_24kitchen(elm, elm_text)"},
           'pages'  : [
               "All Categories",
               "https://www.24kitchen.nl/recepten"
               ]
           },
        'categorie_page' : {
           'taxonomy' : {'type': 'text', 'sels' : ["div.search-filter-select.active"]},
           'links' : {'type': 'text-array:href', 'sels' : ["div.search-content a.full-click-link"]},
           'next_page' : {'scroll' : True},
           'pages'  : [
                ("Pasta", "https://www.24kitchen.nl/recepten/pasta-100"),
                ("Ovenschotel", "https://www.24kitchen.nl/recepten/ovenschotel-101"),
                ("Rijst", "https://www.24kitchen.nl/recepten/rijst-102"),
                ("Aardappelen", "https://www.24kitchen.nl/recepten/aardappel-103"),
                ("Groente", "https://www.24kitchen.nl/recepten/groenten-104"),
                ("Eieren", "https://www.24kitchen.nl/recepten/eigerechten-105"),
                ("Koekjes", "https://www.24kitchen.nl/recepten/koekjes-28"),
                ("Salades", "https://www.24kitchen.nl/recepten/salades-27"),
                ("Sauzen", "https://www.24kitchen.nl/recepten/sauzen-32"),
                ("Soepen", "https://www.24kitchen.nl/recepten/soep-26"),
                ("Taart", "https://www.24kitchen.nl/recepten/taarten-cakes-29"),
                ("Brood", "https://www.24kitchen.nl/recepten/brood-36"),
                ("Snacks", "https://www.24kitchen.nl/recepten/zoete-snacks-35"),
                ("Snacks", "https://www.24kitchen.nl/recepten/hartige-snacks-30"),
                ("Bijgerecht", "https://www.24kitchen.nl/recepten/bijgerecht-93"),
                ("Hoofdgerecht", "https://www.24kitchen.nl/recepten/hoofdgerecht-21"),
                ("Voorgerecht", "https://www.24kitchen.nl/recepten/voorgerecht-20"),
                ("Dessert", "https://www.24kitchen.nl/recepten/nagerecht-24"),
                ("Lunch", "https://www.24kitchen.nl/recepten/lunchgerecht-23"),
                ("Ontbijt", "https://www.24kitchen.nl/recepten/ontbijtgerecht-25"),
                ("Snacks", "https://www.24kitchen.nl/recepten/snack-99"),
                ("Arabisch", "https://www.24kitchen.nl/recepten/arabisch-5"),
                ("Australisch", "https://www.24kitchen.nl/recepten/australisch-19"),
                ("Aziatisch", "https://www.24kitchen.nl/recepten/aziatisch-4"),
                ("Belgisch", "https://www.24kitchen.nl/recepten/belgisch-19347"),
                ("Frans", "https://www.24kitchen.nl/recepten/frans-12"),
                ("Indisch", "https://www.24kitchen.nl/recepten/indisch-17"),
                ("Italiaans", "https://www.24kitchen.nl/recepten/italiaans-8"),
                ("Nederlands", "https://www.24kitchen.nl/recepten/nederlands-7"),
                ("Amerikaans", "https://www.24kitchen.nl/recepten/noord-amerikaans-10"),
                ("Oost-Europees", "https://www.24kitchen.nl/recepten/oost-europees-11"),
                ("Scandinavisch", "https://www.24kitchen.nl/recepten/scandinavisch-18"),
                ("Spaans", "https://www.24kitchen.nl/recepten/spaans-13"),
                ("Engels", "https://www.24kitchen.nl/recepten/verenigd-koninkrijk-15"),
                ("Zuid-Afrikaans", "https://www.24kitchen.nl/recepten/zuid-afrikaans-16"),
                ("Zuid-Amerikaans", "https://www.24kitchen.nl/recepten/zuid-amerikaans-14"),
                ("Mediterraans", "https://www.24kitchen.nl/recepten/mediterraans-106"),
                ("Ontbijt", "https://eatertainment.nl/category/recepten/ontbijt/"),
                ("Lunch", "https://eatertainment.nl/category/recepten/lunch-brunch/"),
                ("Voorgerecht", "https://eatertainment.nl/category/recepten/voorgerecht/"),
                ("Hoofdgerecht", "https://eatertainment.nl/category/recepten/hoofdgerechten/"),
                ("Dessert", "https://eatertainment.nl/category/recepten/desserts/"),
                ("Tussendoor", "https://eatertainment.nl/category/recepten/tussendoortjes/"),
                ("Borrelhapje", "https://eatertainment.nl/category/recepten/borrel/"),
                ("Thema", "https://eatertainment.nl/category/thema/"),
               ]
           },
        'recipe_page' : {
            'parser' : parser_sites_recipe["24kitchen.nl"],
            'pages'  : [
                ("Soep", "https://www.24kitchen.nl/recepten/kastanjesoep-met-salieroom-en-crouton-sterren"),
                ("Ovenschotel", "https://www.24kitchen.nl/recepten/wortelovenschotel"),
                ("Hoofdgerecht", "https://www.24kitchen.nl/recepten/gevulde-pasta-met-pesto-en-spinazie"),
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
    sub = request.GET['sub']
    page = request.GET['page']

    logger.info(f"Scrape request for '{page_type}', '{sub}', '{page}'")
    cat_pages = []
    sub_pages = []
    recipe_scrape_results = []

    site = urllib.parse.urlparse(page).netloc.split(':')[0]
    domain = '.'.join(site.split('.')[-2:])
    if domain not in parser_sites:
        return None
    parser_site = parser_sites[domain]
    webdriver_start()

    if page_type == 'index_page':
        if page:
            cat_links = scrape_links(page, parser_site['index_page'])[1]
            for cat_link in cat_links:
                recipe_scrape_results.append(('#', cat_link['anchor'], cat_link['href'], []))
            dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'scrape')
            filename_full = os.path.join(dirname, domain + '.csv')
            with open(filename_full, 'w') as fp:
                #json.dump(recipe_scrape_results, fp, indent=4, separators= (',', ': '))
                fp.write("Site\tCategorie\tLink\n")
                for recipe_scrape_result in recipe_scrape_results:
                    fp.write("{0}\t{1}\t{2}\n".format(domain, recipe_scrape_result[1], recipe_scrape_result[2]))
        else:
            page_type = 'categorie_page'
            cat_pages = parser_site['categorie_page']['pages']
    else:
        if page_type == 'categorie_page':
            cat_pages = [(sub, page)]

    if page_type == 'categorie_page':
        sub_pages = []
        for cat_page in cat_pages:
            categorie_page = cat_page[1]
            logger.info(f"Scrape categorie page '{categorie_page}'")
            sub_links = scrape_links(categorie_page, parser_site['categorie_page'])[1]
            for sub_link in sub_links:
                sub_pages.append((sub, sub_link))
        page_type = 'recipe_page'
    else:
        if page_type == 'recipe_page':
            sub_pages = [(sub, page)]

    for sub_page in sub_pages:
        sub = sub_page[0]
        recipe_page = sub_page[1]
        logger.info(f"Scrape recipe page '{recipe_page}'")
        webdriver_get(recipe_page)
        root_elm = wd.find_element_by_tag_name('html')
        recipe_new, errors = scrape_recipe(root_elm, parser_site['recipe_page']['parser'])
        if len(errors) == 0:
            id = slugify(recipe_page)
            recipe_new['id'] = recipe_page
            if sub and sub not in recipe_new['categories']:
                recipe_new['categories'].append(sub)
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
