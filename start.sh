source /home/python/venv/venv_file_server/bin/activate
# 超时10分钟,防止文件下载超时
gunicorn -w 2 -t 600 -b 0.0.0.0:2048 -D fileServer:app
