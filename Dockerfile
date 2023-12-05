FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /app

COPY requirements.txt /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

# cron setup
RUN apt-get update && apt-get -y install cron
COPY trendyqc_cron /etc/cron.d/trendyqc_cron
# give exe rights on the cron job
RUN chmod 0644 /etc/cron.d/trendyqc_cron
# apply cron job
RUN crontab /etc/cron.d/trendyqc_cron
# create log file
RUN touch /var/log/cron.log
# run the command on container startup
CMD cron && tail -f /var/log/cron.log