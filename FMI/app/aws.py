import os
import io
from datetime import datetime
import requests
from urllib.request import urlopen
import logging
import boto3
from PIL import Image
import hashlib
import email
from email.parser import Parser
from email import policy
import mimetypes
from slugify import slugify
import dhk_app.recipe as recipe
from FMI.settings import BASE_DIR, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from FMI.settings import MEDIA_BUCKET, MEDIA_URL

logger = logging.getLogger(__name__)

def add_review_to_recipe(id):
    recipe_es = recipe.recipe_es_get(id)
    dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'reviews', slugify(id))
    if os.path.isdir(dirname):
        recipe_es_changed = False
        for filename in os.listdir(dirname):
            filename_full = os.path.join(dirname, filename)
            basename, ext = os.path.splitext(filename)
            if ext in [".jpg", ".jpe", ".gif", ".png"] and len(recipe_es['images']) < 10:
                new_image = {'location' : "data/dhk/reviews/{0}/{1}{2}".format(slugify(id), basename, ext),
                         'type' : 'image'}
            for image in recipe_es['images']:
                if image['location'] == new_image['location']:
                    break
            else:
                recipe_es['images'].append(new_image)
                recipe_es_changed = True
            if ext in [".txt"] and len(recipe_es['reviews']) < 10:
                ctime = datetime.fromtimestamp(os.path.getctime(filename_full))
                with open(filename_full, 'r') as file:
                    new_review = {'review': file.read().replace('\n', ''),
                              'review_date': ctime.strftime('%Y-%m-%d'), 'stars': 4, 'user': ""}
                for review in recipe_es['reviews']:
                    if review['review'] == new_review['review']:
                        break
                else:
                    recipe_es['reviews'].append(new_review)
                    recipe_es_changed = True
        if recipe_es_changed:
            result = recipe.recipe_es_put(recipe_es)

def s3_list_mails(bucket_names):
    logger.debug(f"Obtain mails from '{bucket_names}'")
    bucket_objects = []
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3r = session.resource('s3')
    for bucket_name in bucket_names:
        b3r = s3r.Bucket(bucket_name)
        for o3r in b3r.objects.all():
            emailRawString = o3r.get()['Body'].read()
            parser = Parser()
            msg = parser.parsestr(emailRawString.decode("utf-8"))
            to_addr = email.utils.parseaddr(msg['to'])[1]
            from_addr = email.utils.parseaddr(msg['from'])[1]
            subject = msg['subject']
            to_addresses = msg.get('To').split(",")
            body = msg.get_payload()
            if msg.is_multipart():
                counter = 1
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    # Applications should really sanitize the given filename so that an
                    # email message can't be used to overwrite important files
                    filename = part.get_filename()
                    content_type = part.get_content_type()
                    if "review@deheerlijkekeuken.nl" == to_addr:
                        if filename:
                            basename, ext = os.path.splitext(filename)
                        else:
                            basename, ext = ['review-%03d' % (counter), '']
                        if ext == '':
                            ext = mimetypes.guess_extension(part.get_content_type())
                            if not ext:
                                # Use a generic bag-of-bits extension
                                ext = '.bin'
                        filename = slugify(from_addr[:from_addr.find('@')] + '-' + basename) + ext
                        counter += 1
                        dirname = os.path.join(BASE_DIR, 'data', 'dhk', 'reviews', slugify(subject))
                        if not os.path.isdir(dirname):
                            os.makedirs(dirname)
                        if content_type[0:5] == 'image' or content_type == 'text/plain':
                            with open(os.path.join(dirname, filename), 'wb') as fp:
                                fp.write(part.get_payload(decode=True))
                    if part.get_content_type == 'text/plain':
                        body = part.get_payload()
            if "review@deheerlijkekeuken.nl" == to_addr:
                add_review_to_recipe(subject)
            bucket_objects.append({'key' : o3r.key, 'to' : to_addr, 'from' : from_addr, 'subject': subject, 'body': body})
    return bucket_objects

def s3_delete(bucket_name, key):
    logger.debug(f"Delete from bucket '{bucket_name}' key '{key}'")
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3r = session.resource('s3')
    b3r = s3r.Bucket(bucket_name)
    response = b3r.Object(key).delete()
    return response

def s3_list_images(bucket_name, folder_name):
    logger.debug(f"List images from bucket '{bucket_name}' folder '{folder_name}'")
    images = []
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3r = session.resource('s3')
    s3c = s3r.meta.client
    b3r = s3r.Bucket(bucket_name)
    o3rs = b3r.objects.filter(Prefix=folder_name)
    for o3r in o3rs:
        response = s3c.get_object_tagging(Bucket=bucket_name, Key=o3r.key)
        tagset = response.get('TagSet', None)
        tags = {}
        for tag in tagset:
            tags[tag['Key']] = tag['Value']
        if os.path.splitext(o3r.key)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif', '.pdf']:
            images.append({'location' : o3r.key, 'tags': tags})
    return images

def s3_put_image(bucket_name, folder_name, file_name, src, tags=None):
    logger.debug(f"Put image with name '{file_name}' and src '{src}'")
    #s3c = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY) # client instead of resource !!
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3r = session.resource('s3')
    s3c = s3r.meta.client
    b3r = s3r.Bucket(bucket_name)
    if src[0:4] == 'http':
        try:
            image_content = requests.get(url).content
        except Exception as e:
            logger.error(f"Put image with name '{file_name}' and url '{url}' failed - {e}")
            return None
    if src[0:5] == 'data:':
        with urlopen(src) as response:
            image_content = response.read()

    image_file = io.BytesIO(image_content)
    if not file_name:
        file_name = hashlib.sha1(image_content).hexdigest()[:10] + '.jpg'
    image = Image.open(image_file).convert('RGB')
    bytes_io = io.BytesIO()
    image.save(bytes_io, format='JPEG')
    bytes_io.seek(0)
    key = folder_name + file_name
    #s3c.put_object(Bucket=bucket_name, Key=folder_name)
    #s3c.upload_fileobj(bytes_io, MEDIA_BUCKET, key, ExtraArgs={'ContentType': 'image/jpeg'})
    b3r.upload_fileobj(bytes_io, key, ExtraArgs={'ContentType': 'image/jpeg'})
    if tags:
        tags = [{'Key': k, 'Value': v} for k, v in tags.items() ]
        put_tags_response = s3c.put_object_tagging(Bucket=bucket_name, Key=key, Tagging={'TagSet': tags})
    return key

def s3_update_tags(bucket_name, key, tags):
    logger.debug(f"Update tag for key '{key}' with tages '{tags}'")
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3r = session.resource('s3')
    s3c = s3r.meta.client
    b3r = s3r.Bucket(bucket_name)
    tags = [{'Key': k, 'Value': v} for k, v in tags.items() ]
    response = s3c.put_object_tagging(Bucket=bucket_name, Key=key, Tagging={'TagSet': tags})
    return response


