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
from google.cloud import logging

# Stackdriver logging configuration
client = logging.Client()
logger = client.logger('banalyzepicture')

project_id = app.config['PROJECT_ID']
storage_bucket_name = app.config['STORAGE_BUCKET_NAME']
topic_name = app.config['TOPIC_NAME']
topic_name_output = app.config['TOPIC_NAME_OUTPUT']
token = app.config['TOKEN']
upload_folder = app.config['UPLOAD_FOLDER']
label_to_detect = app.config['LABEL_TO_DETECT']
notify_about_all_checks = app.config['NOTIFY_ABOUT_ALL_CHECKS']
detection_score = float(app.config['DETECTION_SCORE'])

## send configuration to logs

print ("Sending configuration to Stackdriver")
logger.log_struct(
		{"message": "banalyzepicture microservice started", 
		"PROJECT_ID": project_id,
		"STORAGE_BUCKET_NAME": storage_bucket_name,
		"TOPIC_NAME": topic_name,
		"TOPIC_NAME_OUTPUT": upload_folder,
		"TOKEN": token,
		"UPLOAD_FOLDER": upload_folder,
		"LABEL_TO_DETECT": label_to_detect,
		"DETECTION_SCORE": detection_score,
		"Hostname": os.uname()[1],
		"OS version": os.uname()[3]
		})

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

def send_message_to_pubsub(message, file_name):
	publisher = pubsub_v1.PublisherClient()

	print ("Sending message {} to topic {}".format(message, topic_name_output))

	logger.log_struct(
		{"message": "Sending PubSub message ...", 
		"PubSub message": message,
		"PubSub topic": topic_name_output,
		"Image name": file_name,
		"Topic path": topic_path
		})

	message = message.encode('utf-8')
	topic_path = publisher.topic_path(project_id, topic_name_output)
	status = publisher.publish(topic_path, message, object=label_to_detect, file_name=file_name)


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
	print('Results of Vision AI check. Search label: {}'.format(label_to_detect))
	score = 0
	other_objects = ""
	for label in labels:

		other_objects = other_objects + label.description + "(" + str(round(label.score, 2)) + "), "
		print(label.description, round(label.score, 2))

		if label.description == label_to_detect:
			score = label.score
	return score, other_objects



@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
	if (request.args.get('token', '') !=token):
		logger.log_text('Incorrect token for pubsub call',severity='WARNING')
		return 'Invalid request', 400
	
	envelope = json.loads(request.data.decode('utf-8'))
	payload = base64.b64decode(envelope['message']['data'])
	MESSAGES.append(payload)

	# download file from blob

	print("Downloading file {} from storage {}".format(payload, storage_bucket_name))
	_payload = payload.decode('utf-8')
	file_name = download_file(storage_bucket_name, _payload)

	ai_score = analyze_picture(file_name)[0]
	other_objects = analyze_picture(file_name)[1]

	_log_message =  "VisionAI results - object: {}, check result: {}".format(label_to_detect, round(ai_score,2))
	print(_log_message)
	logger.log_struct(
		{"message": _log_message, 
		"object to detect": label_to_detect,
		"detection score": round(ai_score,2),
		"image name": file_name,
		"identified objects": other_objects,
		"send notification about all checks": notify_about_all_checks
		})

	if ai_score > float(detection_score):
    		message = "Object: {} identified with probability {} on picture {}".format(label_to_detect, round(ai_score,2), file_name)
    		send_message_to_pubsub(message, file_name)
	else:
		if notify_about_all_checks == "yes":
			message = "Object: {} not detected. Other objects are {}. Picture {}".format(label_to_detect, other_objects, file_name)
			send_message_to_pubsub(message, file_name)

    		
	# delete local copy of file
	print ("Deleting local copy of file {}".format(file_name))
	os.remove(file_name)




	# Returning any 2xx status indicates successful receipt of the message.
	return 'OK', 200


@app.route('/', methods=['GET'])
def index():
	return render_template('index.html', messages=MESSAGES)



if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080, debug=True)