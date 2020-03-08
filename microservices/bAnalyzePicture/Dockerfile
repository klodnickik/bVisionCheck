FROM python:3.7-slim
RUN apt-get update && apt-get upgrade -y

RUN adduser banalyzepicture

WORKDIR /home/banalyzepicture

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY app app
RUN mkdir tmp

COPY banalyzepicture.py config.py ./



ENV FLASK_APP banalyzepicture.py

RUN chown -R banalyzepicture:banalyzepicture ./
USER banalyzepicture

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 banalyzepicture:app