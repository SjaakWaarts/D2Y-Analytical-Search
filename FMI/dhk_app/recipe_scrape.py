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
#Attribute selector     p[class~="special"] (contains value), div[lang|="zh"] (begins with)
#Pseudo-class sels      p:first-child { },
#                       p:nth-child(An+B) (An is group, B is offset in group 2n+1 for odd)
#                       p:nth-child(-n+3) the first three elements
#Pseudo-element sels   p::first-line { }
#Descendant combinator  article p
#Child combinator       article > p
#Adjacent sibling       combinator	h1 + p
#General sibling        combinator	h1 ~ p
#
#XPATH SELECTOR
#Expression	Description
#nodename	Selects all nodes with the name "nodename"
#path /	Selects from the root node
#path //	Selects nodes in the document from the current node that match the selection no matter where they are
#path .	Selects the current node
#path ..	Selects the parent of the current node
#path @	Selects attributes
#
# added evaluater, starts with =

def con_categories_culy(elm, elm_text):
    try:
        elm_text = elm.get_attribute('content')
        elm_text = elm_text.split('/')
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

def con_title(elm, elm_text):
    try:
        elm_text = elm_text[0].upper() + elm_text[1:].lower()
    except:
        elm_text = ""
    return elm_text

parser_site_recipe = {
"culy.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["h1.article__title"], 'con' : "=con_title(elm, elm_text)"},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:published_time']"], 'con' : "=.get_attribute('content')"},
    'author'        : {'type': 'text', 'con' : "culy.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[property='og:description']", "h1.article__title"], 'con' : "=.get_attribute('content')"},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["meta[name='cXenseParse:Taxonomy']"], 'con' : "=con_categories_culy(elm, elm_text)"},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : ["meta[name='cXenseParse:mhu-article_tag']"], 'con' : "=.get_attribute('content')"},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["path=."], 'con' : "=.get_attribute('content')"},
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
        'sels'       : ["path=/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.article__title"], 'con' : "=con_title(elm, elm_text)"},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.ingredients ul"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["path=."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li[itemprop='ingredients']"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["path=."]},
                            'value': {'type' : 'text', 'sels' : ["span.value"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.measure"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : [".article__content:first-child > h2 ~ p"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["path=."]}
                    }
                }
            }
        }
    },
"lekkerensimpel.com" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : ["h1.hero__title"], 'con' : "=con_title(elm, elm_text)"},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:modified_time']"], 'con' : "=.get_attribute('content')"},
    'author'        : {'type': 'text', 'con' : "lekkersimpel.com"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']", "h1.hero__title"], 'con' : "=.get_attribute('content')"},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["div.hide-for-small-only span.recipe__meta-title"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["path=."], 'con' : "=.get_attribute('content')"},
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
        'sels'       : ["path=/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : ["h1.hero__title"], 'con' : "=con_title(elm, elm_text)"},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["div.recipe__necessities", "div.entry__content ul"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["path=."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["li"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["path=."]},
                            'value': {'type' : 'text', 'sels' : ["span.value"], 'cardinality' : '0-1'},
                            'measure': {'type' : 'text', 'sels' : ["span.measure"], 'cardinality' : '0-1'}
                            }
                        }
                    }
                },
            'instructions'  : {
                'type'       : 'nested',
                'sels'       : ["div.entry__content > p:nth-child(n+4)"],
                'properties' : {
                    'instruction' : {'type': 'text', 'sels' : ["path=."], 'con' : "=con_instruction_lekkerensimpel(elm, elm_text)", 'cardinality' : '0-1'}
                    }
                }
            }
        }
    },
"leukerecepten.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : [".page-content__title"], 'con' : "=con_title(elm, elm_text)"},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:modified_time']", "meta[itemprop='datePublished']"], 'con' : "=.get_attribute('content')"},
    'author'        : {'type': 'text', 'con' : "leukerecepten.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']"], 'con' : "=.get_attribute('content')"},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["ul.page-content__meta li:nth-child(-n+3)"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["path=."], 'con' : "=.get_attribute('content')"},
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
        'sels'       : ["path=/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : [".page-content__title"], 'con' : "=con_title(elm, elm_text)"},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["ul.page-content__ingredients-list"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["path=."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["label"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["path=."]},
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
                    'instruction' : {'type': 'text', 'sels' : ["path=."], 'cardinality' : '0-1'}
                    }
                }
            }
        }
    },
"24kitchen.nl" : {
    'id'            : {'type': 'text', 'con' : ""},
    'title'         : {'type': 'text', 'sels' : [".page-content__title"], 'con' : "=con_title(elm, elm_text)"},
    'published_date': {'type': 'date', 'sels' : ["meta[property='article:modified_time']", "meta[itemprop='datePublished']"], 'con' : "=.get_attribute('content')"},
    'author'        : {'type': 'text', 'con' : "leukerecepten.nl"},
    'excerpt'       : {'type': 'text', 'sels' : ["meta[name='description']"], 'con' : "=.get_attribute('content')"},
    'description'   : {'type': 'text', 'sels' : []},
    'categories'    : {'type': 'text-array', 'sels' : ["ul.page-content__meta li:nth-child(-n+3)"]},
    'cuisiness'     : {'type': 'text-array', 'sels' : []},
    'tags'          : {'type': 'text-array', 'sels' : []},
    'images'        : {
        'type'       : 'nested',
        'sels'       : ["meta[property='og:image']"],
        'properties' : {
            'image'     : {'type': 'text', 'con' : "image"},
            'location'  : {'type': 'text', 'sels' : ["path=."], 'con' : "=.get_attribute('content')"},
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
        'sels'       : ["path=/html"],
        'properties' : {
            'title'        : {'type': 'text', 'sels' : [".page-content__title"], 'con' : "=con_title(elm, elm_text)"},
            'ingredients_parts'   : {
                'type'          : 'nested',
                'sels'       : ["ul.page-content__ingredients-list"],
                'properties'    : {
                    'part'          : {'type': 'integer', 'sels' : ["path=."], 'con' : "=0"},
                    'ingredients'   : {
                        'type'      : 'nested',
                        'sels' : ["label"],
                        'properties' : {
                            'ingredient' : {'type': 'text', 'sels' : ["path=."]},
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
                    'instruction' : {'type': 'text', 'sels' : ["path=."], 'cardinality' : '0-1'}
                    }
                }
            }
        }
    }
}

parser_site = {
    "24kitchen.nl" : {
            'recipe_page' : parser_site_recipe["24kitchen.nl"],
        },
    "culy.nl" : {
            'categorie_page' : {'type': 'text-array', 'sels' : ["a.list__link"], 'con' : "=.get_attribute('href')",
                                'next_page' : ["a.next.page-numbers"]},
            'recipe_page' : parser_site_recipe["culy.nl"],
        },
    "lekkerensimpel.com" : {
            'index_page' : {'type': 'text-array', 'sels' : ["div.category-item a"], 'con' : "=.get_attribute('href')"},
            'categorie_page' : {'type': 'text-array', 'sels' : ["a.post-item__anchor"], 'con' : "=.get_attribute('href')"},
            'recipe_page' : parser_site_recipe["lekkerensimpel.com"],
        },
    "leukerecepten.nl" : {
            'index_page' : {'type': 'text-array', 'sels' : ["div.stream-card a"], 'con' : "=.get_attribute('href')"},
            'categorie_page' : {'type': 'text-array', 'sels' : ["div.rhythm-s a.full-link"], 'con' : "=.get_attribute('href')"},
            'recipe_page' : parser_site_recipe["leukerecepten.nl"],
    }
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
    
    wd.get(page)
    # wait for the element to load
    try:
        webdriver.support.ui.WebDriverWait(wd, 5).until(lambda s: s.find_element_by_tag_name("body").is_displayed())
        return wd
    except TimeoutException:
        print("TimeoutException: Element not found")
        return None


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

def scrape_init_value(field_type):
    field_value = ""
    if field_type == 'nested':
        field_value = []
    elif field_type == 'text-array':
        field_value = []
    elif field_type == 'integer':
        field_value = 0
    elif field_type == 'date':
        field_value = datetime.now().strftime('%Y-%m-%d')
    else:
        field_value = ""
    return field_value

def scrape_links(page, field_parser):
    global wd

    links = []
    next_page = True
    pagenr = 0
    while next_page:
        logger.info(f"Scrape links on '{page}'")
        webdriver_get(page)
        root_elm = wd.find_element_by_tag_name('html')
        elms = scrape_elements(root_elm, field_parser.get('sels', []))
        for elm in elms:
            links = scrape_values(elm, field_parser, links)
        elms = scrape_elements(root_elm, field_parser.get('next_page', []))
        if elms:
            page = elms[0].get_attribute('href')
            pagenr = pagenr + 1
            if pagenr > 2:
                next_page = False
        else:
            next_page = False

    return links

def scrape_elements(root_elm, sels, mode="cor"):
    child_elms = []
    if len(sels) == 0:
        return []
    if mode == "cor":
        for sel in sels:
            if sel[0:5] == 'path=':
                elms = root_elm.find_elements_by_xpath(sel[5:])
            else:
                elms = root_elm.find_elements_by_css_selector(sel)
            child_elms.extend(elms)
            if len(elms) > 0:
                break
    else:
        stack = [(root_elm, 0)]
        while len(stack):
            node = stack.pop()
            root_elm = node[0]
            sel = sels[node[1]]
            if sel[0:5] == 'path=':
                elms = root_elm.find_elements_by_xpath(sel[5:])
            else:
                elms = root_elm.find_elements_by_css_selector(sel)
            for elm in elms:
                if node[1] == len(sels) - 1:
                    child_elms.append(elm)
                else:
                    stack.append((elm, node[1] + 1))
    return child_elms

def scrape_values(elm, field_parser, field_value):
    field_type = field_parser.get('type', None)
    # 1. First get text
    elm_text = elm.text
    if elm.text == "": # lazy read or not visible
        elm_text = elm.get_attribute('textContent').strip()
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
                field_value.append(elm_text)
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
        field_type = field_parser.get('type', None)
        field_value = scrape_init_value(field_type)
        sels = field_parser.get('sels', [])
        elms = scrape_elements(root_elm, sels)
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

    logger.info(f"Scrape request for '{page_type}', '{page}'")
    recipe_scrape_results = []

    site = urllib.parse.urlparse(page).netloc.split(':')[0]
    domain = '.'.join(site.split('.')[-2:])
    if domain not in parser_site:
        return None
    webdriver_start()
    if page_type == 'index_page':
        categorie_pages = scrape_links(page, parser_site[domain]['index_page'])
    else:
        categorie_pages = [page]
    if page_type == 'categorie_page':
        recipe_pages = []
        for categorie_page in categorie_pages:
            logger.info(f"Scrape categorie page '{categorie_page}'")
            recipe_pages.extend(scrape_links(categorie_page, parser_site[domain]['categorie_page']))
    else:
        recipe_pages = [page]

    for recipe_page in recipe_pages:
        logger.info(f"Scrape recipe page '{recipe_page}'")
        webdriver_get(recipe_page)
        root_elm = wd.find_element_by_tag_name('html')
        recipe_new, errors = scrape_recipe(root_elm, parser_site[domain]['recipe_page'])
        id = slugify(page)
        if len(errors) == 0:
            recipe_new['id'] = page
            recipe_obj = recipe.Recipe(id, recipe=recipe_new)
            recipe_obj.put()
        recipe_scrape_results.append((id, recipe_new['title'], recipe_page, errors))
    # leave the driver running
    # webdriver_stop()
    context = {
        'recipe_scrape_results'  : recipe_scrape_results,
        }
    return HttpResponse(json.dumps(context), content_type='application/json')
