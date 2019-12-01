FROM python:3.7-slim

RUN adduser bnotify

WORKDIR /home/bnotify

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY app app
RUN mkdir tmp

COPY bnotify.py config.py ./



ENV FLASK_APP bnotify.py

RUN chown -R bnotify:bnotify ./
USER bnotify

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 8 bnotify:app