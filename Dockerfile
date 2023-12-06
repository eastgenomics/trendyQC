FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /app

COPY requirements.txt /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

# cron setup
RUN apt-get -qq update && apt-get -qq -y install cron
COPY trendyqc_cron /etc/cron.d/trendyqc_cron
# give exe rights on the cron job
RUN chmod 0644 /etc/cron.d/trendyqc_cron
# apply cron job
RUN crontab /etc/cron.d/trendyqc_cron
# create log file
RUN touch /var/log/cron.log

# copy the gunicorn/cron script
COPY trendyqc.sh trendyqc.sh
# make it executable
RUN chmod 100 trendyqc.sh
# execute the script when the container is ran
CMD ["./trendyqc.sh"]