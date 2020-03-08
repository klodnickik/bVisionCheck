from dotenv import load_dotenv
load_dotenv()

import os

class Config(object):
    SECRET_KEY = os.environ.get('TOKEN')
    PROJECT_ID = os.environ.get('PROJECT_ID')
    TOPIC_NAME = os.environ.get('TOPIC_NAME')
    TOPIC_NAME_OUTPUT = os.environ.get('TOPIC_NAME_OUTPUT')
    DETECTION_SCORE = os.environ.get('DETECTION_SCORE')
    LABEL_TO_DETECT = os.environ.get('LABEL_TO_DETECT')
    TOKEN = os.environ.get('TOKEN')
    STORAGE_BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
    NOTIFY_ABOUT_ALL_CHECKS = os.environ.get('NOTIFY_ABOUT_ALL_CHECKS')
    DEBUG_LEVEL = os.environ.get('DEBUG_LEVEL')
    
    UPLOAD_FOLDER = 'tmp'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

