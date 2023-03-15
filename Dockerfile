FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir -p /opt/services/trendyqc/src

COPY requirements.txt /opt/services/trendyqc/src/
WORKDIR /opt/services/trendyqc/src
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /opt/services/trendyqc/src
RUN cd trendyqc && python manage.py collectstatic --no-input

EXPOSE 8000
CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", ":8000", "--chdir", "trendyqc", "trendyqc.wsgi:application"]
