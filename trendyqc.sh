#!/bin/bash

# turn on bash's job control
set -me

# collect static command
python trendyqc/manage.py collectstatic --no-input

# Start the primary process and put it in the background
gunicorn -n trendyqc -c ./config/gunicorn/conf.py --bind :8006 --chdir /app/trendyqc trendyqc.wsgi:application &

# cron
cron -f &

# now we bring the primary process back into the foreground
# and leave it there
fg %1