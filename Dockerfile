FROM python:3.7-alpine
MAINTAINER Eyo

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV FLASK_ENV development
ENV FLASK_APP manage.py

RUN mkdir /src
RUN mkdir /instance
WORKDIR /src

COPY ./src /src
COPY ./instance /instance
COPY ./requirements.txt /requirements.txt


RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
      gcc libc-dev linux-headers postgresql-dev

RUN pip install -r /requirements.txt
RUN apk del .tmp-build-deps


RUN adduser -D user
USER user