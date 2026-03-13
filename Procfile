web: gunicorn app:app
websocket: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 websocket_ticks:app
