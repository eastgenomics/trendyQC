# trendyQC
Django app for monitoring trends in MultiQC data

## Environment

The `docker-compose.yml` contains multiple environment variables. These need to be defined before running the docker-compose file.

Please find the description of each variable below:

```env
# VARIABLES USED IN TRENDYQC CONTAINER
# trendyqc settings module
DJANGO_SETTINGS_MODULE=
# dnanexus token with access to all projects
DNANEXUS_TOKEN=
# trendyqc secret production key
TRENDYQC_SECRET_KEY=
# database name in the postgres container
DB_NAME=
# database credentials in the postgres container
DB_USER=
DB_PASSWORD=
# trendyqc host used in the settings.py to define which hosts are allowed
HOST=

# VARIABLES USED IN POSTGRES CONTAINER
# database username to create
POSTGRES_USER=
# database user password
POSTGRES_PASSWORD=
# database name to create
POSTGRES_DB=

# VARIABLES USED IN NGINX CONTAINER
# virtual host for nginx configuration
VIRTUAL_HOST=
# path to the web container
VIRTUAL_PATH=
```

In the end, TrendyQC will be available at the `${VIRTUAL_HOST}/${VIRTUAL_PATH}` on a Trust PC or a laptop on the Trust network.

## How to setup

The dev (10.252.166.183) and prod servers block most URLs. In order to be able to run the containers on the servers, you need to run the docker file locally:

```bash
docker-compose up -d --build
```

Once the containers are running, you need to save the image of the TrendyQC container (the Nginx and Postgres should already be set up on the servers but you can repeat the step to move the Nginx and Postgres images on the servers):

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

When you are setting up the database for the first time, a couple more things are needed to have the view working.

You need to migrate the models to setup the database. First go into the running container for TrendyQC:

```bash
sudo podman exec -it ${name_of_the_trendyqc_container} /bin/bash

# once inside
python trendyqc/manage.py makemigrations trend_monitoring
python trendyqc/manage.py migrate

# initial import of DNAnexus data
python trendyqc/manage.py initial_import -a
```

The initial import step should take at least 20 mins.

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
|  |  |  |- commands
|  |  |  |  |- __init__.py
|  |  |  |  |- _check.py
|  |  |  |  |- _dnanexus_utils_.py
|  |  |  |  |- _multiqc.py
|  |  |  |  |- _parsing_.py
|  |  |  |  |- _tool.py
|  |  |  |  |- initial_import.py
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
|  |  |  |  |- config_readme.md

|  |  |  |- __init__.py

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
|  |  |  |- plot.html

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
```
