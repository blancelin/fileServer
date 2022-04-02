source /home/python/venv/venv_file_server/bin/activate
gunicorn -w 2 -b 0.0.0.0:4288 -D fileServer:app
