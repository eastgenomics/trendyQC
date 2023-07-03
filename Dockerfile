FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /app

COPY requirements.txt /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/
RUN cd trendyqc && python manage.py collectstatic --no-input

EXPOSE 8000
CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", ":8000", "--chdir", "/app/trendyqc", "trendyqc.wsgi:application"]
