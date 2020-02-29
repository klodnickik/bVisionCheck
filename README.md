# bVisionCheck

Python application which allows to identify "object" on the picture and send notification to power user of the application. The application is created to inform me about my dog Bono waiting next to the door but it can be used also to identify other type of objects.

The application uses Google native services like:
- GCR
- Cloud Storage
- Pub/Sub
- Cloud Run


## Application architecture
![bVisionChecker diagram](docs/bVisionChecker.png)

## Installation

1. Create project in GCP
2. Create Cloud Storage for storing pictures

    `gsutil mb -c standard -l europe-west3  gs://bpictures`

3. Activate GCR API

    **Authenticate to Container Registry**

    `gcloud auth configure-docker`

4. Activate Vision API

    `gcloud services enable vision.googleapis.com`


## Others

### Configuration of credentials when you test and develop application locally
1. Create service account
2. Configure local environment variable

`export GOOGLE_APPLICATION_CREDENTIALS="/path/to/keyfile.json"`

## Microservice gGetPicture

This microservice is used to upload picture to Cloud Storage and send message to Pub/Sub topic.

**Environemnt variables:**
- SECRET_KEY 
- PROJECT_ID 
- TOPIC_NAME 
- STORAGE_BUCKET_NAME 

**Build of docker image**

    docker build -t eu.gcr.io/<your-project-id>/bgetpicture:v0.1 .

    docker push eu.gcr.io/<your-project-id>/bgetpicture:v0.1

**Create Cloud Run instance**

gcloud run deploy --image eu.gcr.io/<your-project-id>/bgetpicture:<tag> --platform managed --region europe-west1 --max-instances 2 --service-account <service-account-name> --allow-unauthenticated --set-env-vars PROJECT_ID=<project-id>,STORAGE_BUCKET_NAME=<cloud-storage-name>,TOPIC_NAME=<pub-sub-topic-name>  bgetpicture


## Microservice bNotify

Microservice created to send message to Messanger communicator

https://<microservice-url>/bot - service connected to Facebook Messanger service
https://<microservice-url>/send - service connected to PubSub, handling of push message 


## Change logs

### 0.0.1 initial configuration
- README updated
- Application architecture diagram

### 0.1 (11/25/2019) created bGetPicture microservice
- created first microservice and configuration file (bGetPicture v.0.1)

### 0.2 (11/26/2019) created draft of bAnalyzePicture
- created draft of bAnalyzePicture microservice
  - connected to Vision AI
  - connected to Cloud Storage
  - connected to output Pub/Sub
- created supporitgn service bListener
 - microservice is connected to Stackdriver logs and is used to support development and tests

### 0.3 (02/26/2020) modified notification rules
- introduced new env (NOTIFY_ABOUT_ALL_CHECKS) which allows to decide when notification should be sent
  - value "yes" - PubSub message to bNotify microservice is sent with every AI event. The message contain list of objectes detected on picture
  - value "no" - PubSub message to bNotify is sent only when the object is detected (previous mode)

## Microservice bUploadPicture

This is local microservice which is hosted in private network with camera. The aim of microservice is to compare images (pictures) 
and in case of identification of significant difference, upload the picture to storage bucket and send message to Pub/Sub.

### 0.6 (02/23/2020) created first version of microservice bUploadPictureFromCamera
- created first, working version of microservice
- creation of deployment scripts for deployment of app into local k8s cluster (microk8s)

### 0.7 (02/29/2020)
- implemented Stackdriver logging
- removed not needed variables
