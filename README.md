# trendyQC
Django app for monitoring trends in MultiQC data

## How to run

```bash
docker-compose up -d --build
```

## env file

The env file should be named `.env` and placed at the root of the project. It should contain the following keys:

```
# dnanexus token with access to all projects
DNANEXUS_TOKEN=
# trendyqc secret production key
TRENDYQC_SECRET_KEY=
# trendyqc settings module
DJANGO_SETTINGS_MODULE=
# trendyqc host
HOST=
# python path to add to the trendyqc container
PYTHONPATH=
```

## Project structure

```
|- trendyqc
|  |- logs
|  |- static
|  |- trend_monitoring
|  |- trendyqc
|  |- manage.py
|- config
|  |- db
|  |- gunicorn
|  |- nginx
|- config
|- .env
|- Dockerfile
|- docker-compose.yml
|- requirements.txt
```
