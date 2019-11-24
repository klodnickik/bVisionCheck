FROM python:3.7-slim

RUN adduser bgetpicture

WORKDIR /home/bgetpicture

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY app app

COPY bgetpicture.py config.py ./



ENV FLASK_APP bgetpicture.py

RUN chown -R bgetpicture:bgetpicture ./
USER bgetpicture

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 8 bgetpicture:app