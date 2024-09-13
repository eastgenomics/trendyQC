# trendyQC
Django app for monitoring trends in MultiQC data using Python 3.8. It is comprised of 3 docker containers:

- trendyqc_db: Postgres database for containing the data
- trendyqc: Django web app which contains the backend and frontend as well as providing the importing functionality
- trendyqc_proxy: Nginx web proxy in order to function in the prod/dev servers of the bioinformatics team

## Environment

The `docker-compose.yml` needs multiple environment variables. These need to be defined before running the docker-compose file.

Please find the description of each variable below:

```env
# VARIABLES USED IN TRENDYQC CONTAINER
# trendyqc settings module
DJANGO_SETTINGS_MODULE
# dnanexus token with access to all projects
DNANEXUS_TOKEN
# trendyqc secret production key
TRENDYQC_SECRET_KEY
# database name in the postgres container
DB_NAME
# database credentials in the postgres container
DB_USER
DB_PASSWORD
# trendyqc host used in the settings.py to define which hosts are allowed
HOST
# slack token for sending messages using Hermes bot
SLACK_TOKEN
# slack channel to send messages to
SLACK_CHANNEL
# LDAP credentials
BIND_DN
BIND_PASSWORD
# URI of the LDAP server
AUTH_LDAP_SERVER_URI
# search parameters
LDAP_CONF
# debug mode boolean (don't run with debug turned on in production)
DEBUG

# VARIABLES USED IN POSTGRES CONTAINER
# database username to create
POSTGRES_USER
# database user password
POSTGRES_PASSWORD
# database name to create
POSTGRES_DB

# VARIABLES USED IN NGINX CONTAINER
# virtual host for nginx configuration
VIRTUAL_HOST
# path to the web container
VIRTUAL_PATH
```

In the end, TrendyQC will be available at the `${VIRTUAL_HOST}/${VIRTUAL_PATH}` on a Trust PC or a laptop on the Trust network.

## How to setup

### Setup the config files for the containers

Each docker container has a config file. These config files need to be located as the following:

- docker-compose.yml
- config
  - db
    - qc_trends_db_env
  - nginx
    - conf.d
      - local.conf
  - gunicorn
    - conf.py

The `qc_trends_db_env` file contains the database name and the user setup data:

```txt
POSTGRES_USER=${db_username}
POSTGRES_PASSWORD=${db_pwd}
POSTGRES_DB=${db_name}
```

The `local.conf` file contains the proxy information for proper proxy setup:

```conf
upstream trendyqc {
    # name of the app container
    server trendyqc:${port_to_use};
}

server {

    listen 80;

    location /trendyqc/static/ {
        autoindex on;
        alias /staticfiles/;
    }

    location / {
        proxy_pass http://trendyqc;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

The `conf.py` file contains basic info on for the gunicorn web server:

```py
name = 'trendyqc'
loglevel = 'info'
errorlog = '-'
accesslog = '-'
workers = 2
```

The directory structure need to be respected and placed at the same level as the docker-compose file used to first setup the images.

### Setup the docker stack

The dev and prod servers block most URLs. In order to be able to run the containers on the servers, you need to run the docker-compose file locally:

```bash
docker-compose up -d --build
```

Once the containers are running, you need to save the image of the TrendyQC container (the Nginx and Postgres should already be set up on the servers but you can repeat the following steps with the appropriate image names to move the Nginx and Postgres images on the servers):

```bash
docker save ${name_of_container} | gzip > ${tar_name}.tar.gz
```

You can then upload the tar file on DNAnexus. You can use `project-GQ8py884gkQZV13z7G7qbK2g` for this purpose.

The next step is to download the tar onto the server and load the image using the following command:

```bash
sudo env "TMPDIR=/appdata/podman/tmp" podman load -i trendyqc.tar.gz --root /appdata/podman/storage
```

And finally you can run the docker-compose file to start the containers.

```bash
sudo podman-compose up -d
```

## Data import

MultiQC reports are extracted from 002 projects in DNAnexus and will be parsed by the TrendyQC app which will store it in the Postgres database.

### Setup import

When you are setting up the database for the first time, a couple more things are needed to have the view working.

You need to migrate the models to setup the database. First go into the running container for TrendyQC:

```bash
sudo podman exec -it ${name_of_the_trendyqc_container} /bin/bash

# once inside
python trendyqc/manage.py makemigrations trend_monitoring
python trendyqc/manage.py migrate
```

### Add reports to TrendyQC

You can also add projects in TrendyQC using the following commands:

```bash
# add all 002 projects
python trendyqc/manage.py add_projects -a
# add specific projects
python trendyqc/manage.py add_projects -p_id ${project_id} [${project_id} ${project_id}]
# import new projects (created 48h ago at the latest)
python trendyqc/manage.oy add_projects -t=-48h
```

The initial import step should take at least 20 mins but the duration is variable and depends on the number of MultiQC reports the code found and are eligible to be imported.

Additionally, reports already present in the database will be skipped (project_id + file_id check)

## Unittesting

Unittesting has been implemented for the TrendyQC app in order to insure the parsing of the MultiQC reports is correct.

In order to run the suite of tests, the user needs to access the TrendyQC container:

```bash
sudo podman exec -it ${name_of_the_trendyqc_container} /bin/bash

# once inside
python trendyqc/manage.py test trend_monitoring.tests
```

## Project structure

```tree
|- trendyqc
|  |- logs
|  |- static

|  |- trend_monitoring
|  |  |- backend_utils
|  |  |  |- __init__.py
|  |  |  |- filtering.py
|  |  |  |- plot.py
|  |  |  |- readme.md

|  |  |- management
|  |  |  |- __init__.py

|  |  |  |- commands
|  |  |  |  |- utils
|  |  |  |  |  |- __init__.py
|  |  |  |  |  |- _check.py
|  |  |  |  |  |- _dnanexus_utils_.py
|  |  |  |  |  |- _multiqc.py
|  |  |  |  |  |- _notifications.py
|  |  |  |  |  |- _parsing_.py
|  |  |  |  |  |- _report.py
|  |  |  |  |  |- _tool.py
|  |  |  |  |  |- _utils.py
|  |  |  |  |- add_projects.py
|  |  |  |  |- readme.md

|  |  |  |- config
|  |  |  |  |- tool_configs
|  |  |  |  |  |- bcl2fastq.json
|  |  |  |  |  |- custom_coverage.json
|  |  |  |  |  |- fastqc.json
|  |  |  |  |  |- happy.json
|  |  |  |  |  |- picard.json
|  |  |  |  |  |- samtools.json
|  |  |  |  |  |- somalier.json
|  |  |  |  |  |- sompy.json
|  |  |  |  |  |- vcfqc.json
|  |  |  |  |  |- verifybamid.json

|  |  |  |  |- assays.json
|  |  |  |  |- displaying_data.json
|  |  |  |  |- sample_read_tools.json
|  |  |  |  |- config_readme.md

|  |  |- models
|  |  |  |- __init__.py
|  |  |  |- bam_qc.py
|  |  |  |- fastq_qc.py
|  |  |  |- filters.py
|  |  |  |- metadata.py
|  |  |  |- vcf_qc.py

|  |  |- templates
|  |  |  |- base.html
|  |  |  |- dashboard.html
|  |  |  |- login.html
|  |  |  |- plot.html

|  |  |- tests
|  |  |  |- test_data
|  |  |  |- test_reports
|  |  |  |- __init__.py
|  |  |  |- custom_tests.py
|  |  |  |- test_filtering.py
|  |  |  |- test_multiqc.py
|  |  |  |- test_plotting.py
|  |  |  |- test_tool.py
|  |  |  |- test_views.py

|  |  |- admin.py
|  |  |- apps.py
|  |  |- forms.py
|  |  |- tables.py
|  |  |- tests.py
|  |  |- urls.py
|  |  |- views.py

|  |- trendyqc
|  |- manage.py

|- config
|  |- db
|  |- gunicorn
|  |- nginx

|- Dockerfile
|- docker-compose.yml
|- requirements.txt
|- trendyqc_cron
|- trendyqc.sh
```
