web: gunicorn app:app
websocket: gunicorn --worker-class eventlet -w 1 websocket_ticks:app
