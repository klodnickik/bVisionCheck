from dotenv import load_dotenv
load_dotenv()

import os

class Config(object):
    PROJECT_ID = os.environ.get('PROJECT_ID')
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
    TOKEN = os.environ.get('TOKEN')


