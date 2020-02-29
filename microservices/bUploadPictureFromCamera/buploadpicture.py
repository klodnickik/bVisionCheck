from dotenv import load_dotenv
import urllib.request as req
import imgcompare
#import logging
import sys
import time
import os
from datetime import datetime
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import logging

# Stackdriver logging configuration
client = logging.Client()
logger = client.logger('buploadpicture')

# load env variables in case of local tests
load_dotenv()

# load values of all environments
project_id = os.environ.get('PROJECT_ID')
img_url = os.environ.get('IMG_URL')
IMG_COMP_RESULT = float(os.environ.get('IMG_COMP_RESULT'))
SLEEP_TIME  = int(os.environ.get('SLEEP_TIME_IN_SECONDS'))
storage_bucket_name = os.environ.get('STORAGE_BUCKET_NAME')
topic_name = os.environ.get('TOPIC_NAME')


def publish_file(file_name, img_comp_percentage):
    logger.log_text('Sending file for AI processing ...')
    start_time = time.time()
    print("<> File sent for AI processing. Difference is {}".format(img_comp_percentage))

    # create copy of file with timestamp
    full_path_of_file = os.path.dirname(os.path.abspath(__file__)) + "/" + file_name
    new_name_of_file = 'img-obj-detected-%s.jpg'%datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    full_path_new_name_of_file = os.path.dirname(os.path.abspath(__file__)) + "/tmp/" + new_name_of_file
    os.system('cp {} {}'.format(full_path_of_file,full_path_new_name_of_file))  

    # upload file to bucket
    img_upload_start_time = time.time()
    file_url = upload_file_to_storage(new_name_of_file)

    # generare Pub/Sub message to initate AI processing
    pubsub_start_time = time.time()
    send_message_to_pubsub(file_url)

    # calculate processing time
    _overalltime = round(time.time() - start_time,2)
    _img_upload_time = round(time.time() - img_upload_start_time,2)
    _pubsub_message_time = round(time.time() - pubsub_start_time,2)

    # send logs to stackdriver
    logger.log_struct(
            {"message": "Image sent for AI (overall time {} seconds, detection score {})".format(_overalltime, img_comp_percentage), 
            "image name": new_name_of_file,
            "detection score": img_comp_percentage,
            "time needed to upload file to bucket": _img_upload_time,
            "time needed to send PubSub message": _pubsub_message_time,
            "img url in bucket": file_url
            })

def compare_file():

    # download new image
    req.urlretrieve(img_url, "tmp/new_image.jpg")

    # check if previous image exists
    if os.path.isfile('tmp/old_image.jpg'):
        # previous file exists, compare old and new pictures 
        img_comp_percentage = imgcompare.image_diff_percent("tmp/old_image.jpg", "tmp/new_image.jpg")
        #logging.info("Img compare result: " + str(img_comp_percentage) + " (expected: " + str(IMG_COMP_RESULT) + ")")
    else:
        # previous file does not exist, comparison will be with next run of the job
        #logging.info("Previous version of image does not exist.")
        img_comp_percentage = 0

    return round(img_comp_percentage,1)

def upload_file_to_storage(filename):

        client = storage.Client(project=project_id)
        bucket = client.get_bucket(storage_bucket_name)

        blob = bucket.blob(filename)
        blob.upload_from_filename(filename='tmp/'+filename)
        blob_file_url = blob.public_url
        print("File {} uploaded to storage bucket".format(filename))

        return (blob_file_url)


def send_message_to_pubsub(message):
    publisher = pubsub_v1.PublisherClient()

    message = message.encode('utf-8')
    topic_path = publisher.topic_path(project_id, topic_name)
    status = publisher.publish(topic_path, message, source='buploadpicture' )

    print("Message sent to Pub/Sub topic {}".format(topic_name))


def main():

    pod_start_time = time.time()
    # logging 
    print("<<< >>> Starting processing. Frequency of job: every {} seconds, configured image comparison factor is {}".format(SLEEP_TIME, IMG_COMP_RESULT))
    logger.log_struct(
            {"message": "bUploadPicture - starting microservice", 
            "Frequency of job in seconds": SLEEP_TIME, 
            "image comparison factor is": IMG_COMP_RESULT, 
            "image source url": img_url, 
            "destination storage bucket": storage_bucket_name,
            "pubsub topic name": topic_name
            } )

    ########### main loop
    counter = 0 # list of processing cycles
    statistics_sent_counter = 0 # counter value when last statistics were sent
    sent_for_ai_counter = 0 # pictures sent for ai processing
    sum_img_comp_percentage = 0 # variable for average img comparison calculation

    while True:
        counter = counter + 1
        # download and compare images
        img_comp_percentage = compare_file()

        # if the result of comparison meets the treshold - send file for processing
        if img_comp_percentage > IMG_COMP_RESULT:
            publish_file("tmp/new_image.jpg", img_comp_percentage)
            sent_for_ai_counter = sent_for_ai_counter + 1
            sum_img_comp_percentage = sum_img_comp_percentage + img_comp_percentage


        # rename images (change new image into old one)
        os.rename("tmp/new_image.jpg","tmp/old_image.jpg")


        # delete old files - older then 2 days
        path = 'tmp/'
        for filename in os.listdir(path):
            if os.path.getmtime(os.path.join(path, filename)) < time.time() - 2 * 86400:
                if os.path.isfile(os.path.join(path, filename)):
                    os.remove(os.path.join(path, filename))
                    print (" deleted old file {}".format(filename))
                    logger.log_text('Deleted old picture: '.format(filename))

        # statistics
        if counter > statistics_sent_counter + int((round((3600 / SLEEP_TIME),0))) :
            _podlife = round((time.time() - pod_start_time) / 3600, 0) # calculate life of pod in hours

            # calculate average score for img difference detection
            if sum_img_comp_percentage > 0:
                ave_img_comp_percentage = round(sum_img_comp_percentage / sent_for_ai_counter, 2)
            else:
                ave_img_comp_percentage = 0

            logger.log_struct(
                    {"message": "bUploadPicture - heartbeat - statistics (hours {}) ".format(_podlife), 
                    "Frequency of job in seconds": SLEEP_TIME, 
                    "image comparison detector is": IMG_COMP_RESULT,
                    "pod life in hours": _podlife,
                    "pictures analyzed": counter,
                    "pictures sent for AI": sent_for_ai_counter,
                    "average image difference factor": ave_img_comp_percentage
                    } )
            statistics_sent_counter = counter

        # wait for next check
        time.sleep(SLEEP_TIME)


if __name__ == "__main__": main()

