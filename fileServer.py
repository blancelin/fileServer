import os
import json
import time
import socket
from threading import Timer
from urllib import request as rq
from utils.algorithm import mine_decrypt
from utils.logServer import blance_logging
from flask import Flask, render_template, \
    request, jsonify, send_from_directory
from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    """
        将正则表达式的参数保存到对象属性中
    """

    def __init__(self, url_map, regex):
        # flask会使用这个属性来进行路由的正则匹配
        super().__init__(url_map)
        self.regex = regex


app = Flask(__name__)
app.url_map.converters["re"] = RegexConverter
# 支持中文
app.config['JSON_AS_ASCII'] = False
# 公网ip
HOST = json.loads(rq.urlopen("https://api.ipify.org/?format=json").read())["ip"]
# 局域网ip
# HOST = socket.gethostbyname(socket.gethostname())
# 端口
PORT = int(mine_decrypt("D7CDBDE0F480237F0240944C6E827763AADFB4EF8980227D9CD2727685E1DAB5"))
# 服务根路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 文件存储路径
SAVE_PATH = os.path.join(BASE_DIR, "files")
# 实例化日志对象
log = blance_logging()


# 文件上传，返回：{"status": True, "fileUrl": ""}
@app.route('/<re("index|fileUpload"):url>', methods=["GET", "POST"])
def upload(url):
    # 来源地址
    ip = request.remote_addr
    if request.method == "POST":
        f = request.files["file"]
        upload_path = os.path.join(SAVE_PATH, f.filename)
        f.save(upload_path)
        file_url = f"http://{HOST}:{PORT}/download/{f.filename}"
        # file_url = f"http://{HOST}/download/{f.filename}"
        # 埋入日志
        log.info(f"upload file_url {file_url} by {ip}")
        return jsonify({"status": True, "message": file_url})
    # 埋入日志
    log.info(f"request index page by {ip}")
    return render_template("fileServer.html")


# 文件下载
@app.route("/download/<path:filename>")
def download(filename):
    # 来源地址
    ip = request.remote_addr
    # 判断文件是否存在
    if filename in os.listdir(SAVE_PATH):
        # 埋入日志
        log.info(f"download filename {filename} by {ip}")
        return send_from_directory(SAVE_PATH, filename, as_attachment=True)
    # 埋入日志
    log.warning(f"download filename {filename} by {ip} is failed")
    return jsonify({"status": False, "message": "the filename is not exists"})


# 文件详情
@app.route('/<re("fileDetail|fileDate"):url>', methods=["GET"])
def detail(url):
    # 来源地址
    ip = request.remote_addr
    if url == "fileDate":
        filenames = os.listdir(SAVE_PATH)
        files = [os.path.join(SAVE_PATH, item) for item in filenames]
        file_list = []
        for file in files:
            file_date = os.path.getmtime(file)
            file_name = os.path.basename(file)
            file_size = os.path.getsize(file)
            file_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_date))
            file_link = f"http://{HOST}:{PORT}/download/{file_name}"
            # file_link = f"http://{HOST}/download/{file_name}"
            file_list.append(
                {"fileSize": file_size, "fileDate": file_date, "fileName": file_name, "fileUrl": file_link})
        # 按日期倒序
        file_list = sorted(file_list, key=lambda item: item["fileDate"], reverse=True)
        # 转json格式，支持中文
        file_list = json.dumps(file_list, ensure_ascii=False)
        # 埋入日志
        log.info(f"request size {len(file_list)}b by {ip}")
        return jsonify({"status": True, "message": file_list})
    # 埋入日志
    log.info(f"request detail page by {ip}")
    return render_template("fileDetail.html")


# 预留一个文件删除接口
@app.route("/fileDel/<path:filename>", methods=["DELETE"])
def delete(filename):
    # 来源地址
    ip = request.remote_addr
    try:
        filename = mine_decrypt(filename)
        if filename in os.listdir(SAVE_PATH):
            os.remove(os.path.join(SAVE_PATH, filename))
            # 埋入日志
            log.warning(f"delete filename {filename} by {ip}")
            return jsonify({"status": True, "message": "delete success"})
        # 埋入日志
        log.warning(f"delete filename {filename} by {ip} is failed")
        return jsonify({"status": False, "message": f"the filename is not exists"})
    except Exception as e:
        log.error(f"delete filename {filename} by {ip} is error")
        return jsonify({"status": False, "message": f"the filename delete failed: {e}"})


# 404.html
@app.errorhandler(404)
def miss(e):
    log.warning(f"request 404 page by {request.remote_addr}")
    return render_template("404.html"), 404


# 文件定时清理
def file_remove_handle():
    """
        清理规则：大于500开始清理
    """
    filenames = os.listdir(SAVE_PATH)
    # {"文件名": "时间", ...}
    file_map = {os.path.join(SAVE_PATH, item): time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
        os.path.getmtime(os.path.join(SAVE_PATH, item)))) for item in filenames}
    # 按时间倒叙排列文件
    file_list = sorted(file_map, key=lambda item: file_map[item], reverse=True)
    # 待清理的文件列表
    clean_file_list = file_list[500:] if len(file_list) >= 500 else []
    # 清理文件
    for filename in clean_file_list:
        try:
            os.remove(filename)
            log.info(f"delete {filename} success")
        except Exception as e:
            log.error(f"delete {filename} failed * {e}")
            continue


# 定时清理函数
def clean_file_handle():
    log.info(f"start clean server file...")
    file_remove_handle()
    t = Timer(function=clean_file_handle, interval=1800)
    t.start()


# 前端跑马灯提示

if __name__ == '__main__':
    """
        本地 || 服务器 运行只用切换公网和局域网IP
    """
    clean_file_handle()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
