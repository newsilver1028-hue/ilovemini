#!/bin/sh
set -eu
python manage.py migrate --noinput
python manage.py bootstrap_superuser
python manage.py collectstatic --noinput
if [ "${SYNC_ILOVEMINI_PARTNERS:-0}" = "1" ]; then
  python manage.py sync_ilovemini_partners
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 60
