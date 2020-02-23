from dotenv import load_dotenv
import urllib.request as req
import imgcompare
import logging
import sys
from datetime import datetime
from google.cloud import storage
from google.cloud import pubsub_v1

load_dotenv()

# logging

logging.basicConfig(        filemode='a',
                            format='%(asctime)s,%(name)s %(levelname)s %(message)s',
                            datefmt='%m/%d %H:%M:%S',
                            level=logging.INFO,
                            stream=sys.stdout)


import os, time

project_id = os.environ.get('PROJECT_ID')
IMG_URL = os.environ.get('IMG_URL')
DEST_URL = os.environ.get('DEST_URL')
IMG_COMP_RESULT = float(os.environ.get('IMG_COMP_RESULT'))
SLEEP_TIME  = int(os.environ.get('SLEEP_TIME_IN_SECONDS'))
storage_bucket_name = os.environ.get('STORAGE_BUCKET_NAME')
topic_name = os.environ.get('TOPIC_NAME')


def publish_file(file_name, DEST_URL, img_comp_percentage):
    logging.info("<> File is being sent for AI processing. Difference is " + str(img_comp_percentage))
    print("<> File sent for AI processing. Difference is {}".format(img_comp_percentage))

    # create copy of file with timestamp
    full_path_of_file = os.path.dirname(os.path.abspath(__file__)) + "/" + file_name
    new_name_of_file = 'img-obj-detected-%s.jpg'%datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    full_path_new_name_of_file = os.path.dirname(os.path.abspath(__file__)) + "/tmp/" + new_name_of_file
    os.system('cp {} {}'.format(full_path_of_file,full_path_new_name_of_file))  

    # upload file to bucket
    file_url = upload_file_to_storage(new_name_of_file)

    # generare Pub/Sub message to initate AI processing
    send_message_to_pubsub(file_url)


def compare_file():

    # download new image
    req.urlretrieve(IMG_URL, "tmp/new_image.jpg")

    # check if previous image exists
    if os.path.isfile('tmp/old_image.jpg'):
        # previous file exists, compare old and new pictures 
        img_comp_percentage = imgcompare.image_diff_percent("tmp/old_image.jpg", "tmp/new_image.jpg")
        logging.info("Img compare result: " + str(img_comp_percentage) + " (expected: " + str(IMG_COMP_RESULT) + ")")
    else:
        # previous file does not exist, comparison will be with next run of the job
        logging.info("Previous version of image does not exist.")
        img_comp_percentage = 0

    return round(img_comp_percentage,1)

def upload_file_to_storage(filename):

        client = storage.Client(project=project_id)
        bucket = client.get_bucket(storage_bucket_name)

        blob = bucket.blob(filename)
        blob.upload_from_filename(filename='tmp/'+filename)
        blob_file_url = blob.public_url
        _log_info = "<> file {} uploaded to blob with URL: {}".format(filename, blob_file_url)
        print (_log_info)
        logging.info(_log_info)

        return (blob_file_url)


def send_message_to_pubsub(message):
    publisher = pubsub_v1.PublisherClient()

    message = message.encode('utf-8')
    topic_path = publisher.topic_path(project_id, topic_name)
    status = publisher.publish(topic_path, message, source='buploadpicture' )

    _log_info = "<> message sent to Pub/Sub topic {}".format(topic_name)
    print (_log_info)
    logging.info(_log_info)

def main():

    _message = "<<< >>> Starting processing. Frequency of job: every {} seconds, configured image comparison factor is {}".format(SLEEP_TIME, IMG_COMP_RESULT)

    print(_message)
    logging.info(_message)


    while True:
        # download and compare images
        img_comp_percentage = compare_file()

        # if the result of comparison meets the treshold - send file for processing
        if img_comp_percentage > IMG_COMP_RESULT:
            publish_file("tmp/new_image.jpg", DEST_URL, img_comp_percentage)

        # rename images (change new image into old one)
        os.rename("tmp/new_image.jpg","tmp/old_image.jpg")

        # delete old files - older then 2 days
        path = 'tmp/'
        for filename in os.listdir(path):
            # if os.stat(os.path.join(path, filename)).st_mtime < now - 7 * 86400:
            if os.path.getmtime(os.path.join(path, filename)) < time.time() - 2 * 86400:
                if os.path.isfile(os.path.join(path, filename)):
                    os.remove(os.path.join(path, filename))
                    _message = " deleted old file {}".format(filename)
                    print(_message)
                    logging.info(_message)

        # wait for next check
        time.sleep(SLEEP_TIME)


if __name__ == "__main__": main()

