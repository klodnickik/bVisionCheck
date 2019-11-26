import os
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename


# Imports the Google Cloud client library
import google.cloud.logging

# Instantiates a client
client = google.cloud.logging.Client()

# Connects the logger to the root logging handler; by default this captures
# all logs at INFO level and higher
client.setup_logging()
# Imports Python standard library logging
import logging

project_id = app.config['PROJECT_ID']

## print configuration

logging.warning("bListener starting ...")

	
@app.route('/')
def request_handling():
	
	logging.warning('Arguments: {}'.format(request.args))
	logging.warning('Method: {}'.format(request.method))
	logging.warning('URL: {}'.format(request.url))

	if request.method == 'POST':  
		result = request.form
		logging.warning(result) 

	return "ok"



if __name__ == "__main__":
	app.run()