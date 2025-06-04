web: gunicorn "src.app_final_vue:create_app()" --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent --timeout 120
worker: python -m celery -A src.tasks.celery worker --loglevel=info
