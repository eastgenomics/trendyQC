FROM python:3.12

ENV PYTHONUNBUFFERED 1

RUN mkdir /app && \
    apt-get update -y && \
    apt-get install -y libldap2-dev libsasl2-dev ldap-utils

COPY requirements.txt /app/
WORKDIR /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    echo "Delete python cache directories" 1>&2 && \
    find /usr/local/lib/python3.12 \( -iname '*.c' -o -iname '*.pxd' -o -iname '*.pyd' -o -iname '__pycache__' \) | \
    xargs rm -rf {}

COPY . /app/

# cron setup
RUN apt-get -qq update && apt-get -qq -y install cron
COPY trendyqc_cron /etc/cron.d/trendyqc_cron
# give exe rights on the cron job
RUN chmod 0644 /etc/cron.d/trendyqc_cron && \
    # apply cron job
    crontab /etc/cron.d/trendyqc_cron && \
    # create log file
    touch /var/log/cron.log && \
    # fix the cron job: https://stackoverflow.com/questions/21926465/issues-running-cron-in-docker-on-different-hosts
    cat /etc/pam.d/cron | sed -e "s/required     pam_loginuid.so/optional     pam_loginuid.so/g" > /tmp/cron && mv /tmp/cron /etc/pam.d/cron && \
    # make Grafana script executable
    chmod 100 trendyqc_grafana.sh

# copy the gunicorn/cron script
COPY trendyqc.sh trendyqc.sh
# make it executable
RUN chmod 100 trendyqc.sh
# execute the script when the container is ran
CMD ["./trendyqc.sh"]