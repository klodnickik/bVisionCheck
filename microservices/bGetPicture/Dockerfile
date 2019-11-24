FROM python:3.7.4-alpine

RUN adduser -D bgetpicture

WORKDIR /home/bgetpicture

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app

COPY bgetpicture.py config.py boot.sh ./
RUN chmod +x boot.sh



ENV FLASK_APP nagradzacz.py

RUN chown -R nagradzacz:nagradzacz ./
USER nagradzacz

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]