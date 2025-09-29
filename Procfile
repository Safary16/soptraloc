web: cd soptraloc_system && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --log-file -
worker: cd soptraloc_system && celery -A config worker -l info
beat: cd soptraloc_system && celery -A config beat -l info
release: cd soptraloc_system && python manage.py migrate