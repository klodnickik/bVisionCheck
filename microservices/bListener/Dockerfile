FROM python:3.7-slim

RUN adduser blistener

WORKDIR /home/blistener

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY app app
RUN mkdir tmp

COPY blistener.py config.py ./



ENV FLASK_APP blistener.py

RUN chown -R blistener:blistener ./
USER blistener

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 8 blistener:app