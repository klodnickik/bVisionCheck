import os, io
import urllib.request
#from app import app
from flask import Flask, flash, request, redirect, render_template


from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import vision
from google.cloud.vision import types


#project_id = app.config['PROJECT_ID']
#storage_bucket_name = app.config['STORAGE_BUCKET_NAME']
#topic_name = app.config['TOPIC_NAME']
#secret_key = app.config['SECRET_KEY']
#upload_folder = app.config['UPLOAD_FOLDER']
#max_content_length = app.config['MAX_CONTENT_LENGTH']

## print configuration

#print ("bVisionCheck starting ...")
#print ("configuration details:")
#print ("- PROJECT_ID: {}".format(project_id))
#print ("- STORAGE_BUCKET_NAME: {}".format(storage_bucket_name))
#print ("- TOPIC_NAME: {}".format(topic_name))
#print ("- SECRET_KEY: {}".format(secret_key))
#print ("- UPLOAD_FOLDER: {}".format(upload_folder))
#print ("- MAX_CONTENT_LENGTH: {}".format(max_content_length))


file_path = 'https://storage.cloud.google.com/bpictures/DSC02531.JPG'
storage_bucket_name = 'bpictures'
upload_folder = 'tmp'
looking_for_label ='Dog'
looking_for_score = 0.85
topic_name_output = 'identified-objects'
project_id = 'bvisioncheck'

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

	print ("Sending message {} to topic {}".format(message, topic_name_output))
	message = message.encode('utf-8')
	topic_path = publisher.topic_path(project_id, topic_name_output)
	status = publisher.publish(topic_path, message, object=looking_for_label)


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
	print('Results of Vision AI check. Search label: {}'.format(looking_for_label))

	score = 0
	for label in labels:
		print(label.description, round(label.score, 2))
		if label.description == looking_for_label:
			score = label.score
	return score



def main():
	print ("Starting Vision AI check ...")

	file_name = download_file(storage_bucket_name, file_path)
	score = analyze_picture(file_name)
	
	if score >= looking_for_score:
		message = '{} identified on picture {} with probability {}'.format(looking_for_label, file_path, round(score, 2))
		send_message_to_pubsub(message)


if __name__ == "__main__":
	main()