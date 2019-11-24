import os
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

from google.cloud import storage
from google.cloud import pubsub_v1

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


project_id = app.config['PROJECT_ID']
storage_bucket_name = app.config['STORAGE_BUCKET_NAME']
topic_name = app.config['TOPIC_NAME']
secret_key = app.config['SECRET_KEY']
upload_folder = app.config['UPLOAD_FOLDER']
max_content_length = app.config['MAX_CONTENT_LENGTH']

## print configuration

print ("bVisionCheck starting ...")
print ("configuration details:")
print ("- PROJECT_ID: {}".format(project_id))
print ("- STORAGE_BUCKET_NAME: {}".format(storage_bucket_name))
print ("- TOPIC_NAME: {}".format(topic_name))
print ("- SECRET_KEY: {}".format(secret_key))
print ("- UPLOAD_FOLDER: {}".format(upload_folder))
print ("- MAX_CONTENT_LENGTH: {}".format(max_content_length))


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_to_storage(filename):

		client = storage.Client(project=project_id)
		bucket = client.get_bucket(storage_bucket_name)
		print ("Uploding file {} to bucket {}".format(filename, storage_bucket_name))

		blob = bucket.blob(filename)
		blob.upload_from_filename(filename=upload_folder + '/' + filename)
		blob_file_url = blob.public_url
		print ("File uploaded with URL: {}".format(blob_file_url))

		return (blob_file_url)


def send_message_to_pubsub(message):
	publisher = pubsub_v1.PublisherClient()

	print ("Sending message {} to topic {}".format(message, topic_name))
	message = message.encode('utf-8')
	topic_path = publisher.topic_path(project_id, topic_name)
	status = publisher.publish(topic_path, message, source='website_form' )

	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
	if request.method == 'POST':
        # check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(upload_folder + '/'+  filename)
			flash('File successfully uploaded')

			# upload file to cloud storage
			file_url = upload_file_to_storage(filename)

			# send message to pubsub (filename)
			send_message_to_pubsub(file_url)

			# delete local copy of file
			print ("Deleting local copy of file {}".format(filename))
			os.remove(upload_folder + '/'+  filename)


			return redirect('/')
		else:
			flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
			return redirect(request.url)

if __name__ == "__main__":
	app.run()