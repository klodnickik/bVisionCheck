FROM python:3.7-slim

RUN adduser buploadpicture

WORKDIR /home/buploadpicture

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir tmp

COPY buploadpicture.py ./


RUN chown -R buploadpicture:buploadpicture ./
USER buploadpicture

CMD ["python3","buploadpicture.py"]
