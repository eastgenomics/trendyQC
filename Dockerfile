FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /app

COPY requirements.txt /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/