import os
import time
import io
import hashlib
import requests
from selenium import webdriver
from PIL import Image

global wd

def fetch_thumbnails(query: str, max_links_to_fetch: int, sleep_between_interactions: float = 0.1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    wd = webdriver.Chrome(options=options)
    # build the google query
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    thumbnails = []
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(
            f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

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

    wd.close()
    wd.quit()
    return thumbnails


def persist_image(folder_path: str, url: str):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path, hashlib.sha1(
            image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")
