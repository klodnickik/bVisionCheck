from dotenv import load_dotenv
load_dotenv()

import os

class Config(object):
    PROJECT_ID = os.environ.get('PROJECT_ID')


