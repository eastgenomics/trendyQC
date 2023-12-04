FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /app

RUN apt-get update -y
RUN apt-get install -y libldap2-dev libsasl2-dev ldap-utils

COPY requirements.txt /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/