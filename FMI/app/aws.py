import os
from datetime import datetime
import boto3
import email
from email.parser import Parser
from email import policy
import mimetypes
from slugify import slugify
import dhk_app.recipe as recipe
from FMI.settings import BASE_DIR, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def add_review_to_recipe(id):
    recipe_es = recipe.get_recipe_es(id)
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
            result = recipe.put_recipe_es(recipe_es)

def list_s3(buckets):
    bucket_objects = []
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3 = session.resource('s3')
    for bucket_name in buckets:
        bucket = s3.Bucket(bucket_name)
        for bo in bucket.objects.all():
            emailRawString = bo.get()['Body'].read()
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
            bucket_objects.append({'key' : bo.key, 'to' : to_addr, 'from' : from_addr, 'subject': subject, 'body': body})
    return bucket_objects