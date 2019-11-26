from dotenv import load_dotenv
load_dotenv()

import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this-is-my-key'
    PROJECT_ID = os.environ.get('PROJECT_ID')
    TOPIC_NAME = os.environ.get('TOPIC_NAME')
    STORAGE_BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
    UPLOAD_FOLDER = 'tmp'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

