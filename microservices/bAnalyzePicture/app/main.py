import os, io
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, render_template
import json
import base64

from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import vision
from google.cloud.vision import types
import google.cloud.logging

client = google.cloud.logging.Client()
client.setup_logging()
import logging

project_id = app.config['PROJECT_ID']
storage_bucket_name = app.config['STORAGE_BUCKET_NAME']
topic_name = app.config['TOPIC_NAME']
topic_name_output = app.config['TOPIC_NAME_OUTPUT']
token = app.config['TOKEN']
upload_folder = app.config['UPLOAD_FOLDER']
label_to_detect = app.config['LABEL_TO_DETECT']
detection_score = float(app.config['DETECTION_SCORE'])

## send configuration to logs

logging.warning("vAnalyzePicture starting ... variable values")
logging.warning("- PROJECT_ID: {}".format(project_id))
logging.warning("- STORAGE_BUCKET_NAME: {}".format(storage_bucket_name))
logging.warning("- TOPIC_NAME: {}".format(topic_name))
logging.warning("- TOPIC_NAME_OUTPUT: {}".format(topic_name_output))
logging.warning("- TOKEN: {}".format(token))
logging.warning("- UPLOAD_FOLDER: {}".format(upload_folder))
logging.warning("- LABEL_TO_DETECT: {}".format(label_to_detect))
logging.warning("- DETECTION_SCORE: {}".format(detection_score))

MESSAGES = []

def download_file(storage_bucket_name, file_path):

	# extract file name 
	_file_path = file_path.split('/')
	file_name = _file_path[-1]

	print ("Downloading file {} from blob {}".format(file_name, storage_bucket_name))
	storage_client = storage.Client()
	bucket = storage_client.get_bucket(storage_bucket_name)
	blob = bucket.blob(file_name)
	blob.download_to_filename(upload_folder + '/' + file_name)
	return (upload_folder + '/' + file_name)

def send_message_to_pubsub(message):
	publisher = pubsub_v1.PublisherClient()

	logging.warning ("Sending message {} to topic {}".format(message, topic_name_output))
	message = message.encode('utf-8')
	topic_path = publisher.topic_path(project_id, topic_name_output)
	status = publisher.publish(topic_path, message, object=label_to_detect)


def analyze_picture(file_name):
	# Instantiates a client
	client = vision.ImageAnnotatorClient()
	# The name of the image file to annotate
	file_name = os.path.abspath(file_name)
	# Loads the image into memory
	with io.open(file_name, 'rb') as image_file:
		content = image_file.read()
	image = types.Image(content=content)
	# Performs label detection on the image file
	response = client.label_detection(image=image)
	labels = response.label_annotations
	logging.warning('Results of Vision AI check. Search label: {}'.format(label_to_detect))
	logging.warning(labels)
	score = 0
	for label in labels:
		print(label.description, round(label.score, 2))
		if label.description == label_to_detect:
			score = label.score
	return score



@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
	if (request.args.get('token', '') !=token):
		return 'Invalid request', 400
	
	envelope = json.loads(request.data.decode('utf-8'))
	payload = base64.b64decode(envelope['message']['data'])
	MESSAGES.append(payload)

	# download file from blob

	logging.warning("Downloading file {} from storage {}".format(payload, storage_bucket_name))
	_payload = payload.decode('utf-8')
	file_name = download_file(storage_bucket_name, _payload)

	ai_score = analyze_picture(file_name)
	if ai_score > float(detection_score):
    		message = "Object: {} identified with probability {} on picture {}".format(label_to_detect, round(ai_score,2), file_name)
    		send_message_to_pubsub(message)
    		
	# delete local copy of file
	logging.warning ("Deleting local copy of file {}".format(file_name))
	os.remove(file_name)




	# Returning any 2xx status indicates successful receipt of the message.
	return 'OK', 200


@app.route('/', methods=['GET'])
def index():
	return render_template('index.html', messages=MESSAGES)



if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080, debug=True)