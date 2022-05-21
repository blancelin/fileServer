import os
import json
import time
import socket


import requests
from threading import Timer
from urllib.parse import quote
from urllib import request as rq
from utils.algorithm import mine_decrypt
from utils.logServer import blance_logging
from utils.mysql_handle import write_func, query_func
from werkzeug.routing import BaseConverter
from flask import Flask, render_template, \
    request, jsonify, send_from_directory, session, make_response


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
# SECRET_KEY
app.config['SECRET_KEY'] = "blance"
# 当前环境
VENV = "local"  # TODO 环境切换时：local or prod
if VENV == "local":
    # 局域网ip
    HOST = socket.gethostbyname(socket.gethostname())
    host = HOST
else:
    # 公网ip
    HOST = json.loads(rq.urlopen("https://api.ipify.org/?format=json").read())["ip"]
    host = "127.0.0.1"
# 端口
PORT = int(mine_decrypt("D7CDBDE0F480237F0240944C6E827763AADFB4EF8980227D9CD2727685E1DAB5"))
# 服务根路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 文件存储路径
BASIC_PATH = os.path.join(BASE_DIR, "files")
# 不存在则新建
os.mkdir(BASIC_PATH) if not os.path.exists(BASIC_PATH) else BASIC_PATH
# 实例化日志对象
log = blance_logging()
# 接入马上登录
secretKey = mine_decrypt("3C7CF66DA16610A1E09B3C12CAF6FD4A35D2B7B4873B00FAAE42A6D459EAE501"
                         "A9D250471C10A074D2314B28A71E0FC2A9D250471C10A074D2314B28A71E0FC2")


# 二维码
@app.route("/mashang/login/qrCodeReturnUrl", methods=["GET"])
def qrcode():
    url = f"https://server01.vicy.cn/8lXdSX7FSMykbl9nFDWESdc6zfouSAEz/wxlogin/wxLogin/tempUserId?secretKey={secretKey}"
    # 默认值
    qrcode_url = "http://login.vicy.cn?tempUserId=5e371810a63b4c54919d108d11ccfda4"
    resp = requests.get(url)
    code = resp.status_code
    msg = resp.json()["message"] if code == 200 else "失败"
    if msg == "成功":
        qrcode_url = resp.json()["data"]["qrCodeReturnUrl"]
        session["qrcode_url"] = qrcode_url
    log.info(f"Get qrcode_url success, {qrcode_url}")
    return jsonify({"qrcode_url": qrcode_url})


# 回调接口
@app.route("/mashang/login/callback", methods=["POST"])
def callback():
    user_id = request.form.get("userId")
    temp_user_id = request.form.get("tempUserId")
    nick_name = request.form.get("nickname", "Guest")
    avatar = request.form.get("avatar", "https://thirdwx.qlogo.cn/mmopen/vi_32/Q3auHgzwzM6npDo4Vgk61VOvQ"
                                        "da0pAh3ccfZyT6A6rW86ciaiaiaNjdQD9LN9xyxhNJLyu7cnUdL0gWdsPGccNcoQ/132")
    ip_addr = request.form.get("ipAddr")
    # 写入sessiontable
    sql = f"insert into sessiontable(tempUserId, userId, nickname, avatar, ipAddr) values({temp_user_id}," \
          f"{user_id}, {nick_name}, {avatar}, {ip_addr});"
    write_func(sql)
    log.info(f"Insert into sessiontable success, {temp_user_id}")
    return jsonify({"status": True, "errcode": 0})


# 登录结果响应
@app.route("/mashang/login/userInfo/<path:temp_user_id>", methods=["GET", "POST"])
def userinfo(temp_user_id):
    # 查询sessiontable
    sql = f"select * from sessiontable where tempUserId='{temp_user_id}' and isActive=1;"
    res = query_func(sql)
    if not res:
        log.warning(f"The guest not login, {temp_user_id}")
        return jsonify({"status": False, "message": "the guest not login"})
    user_id = res["userId"]
    nick_name = res["nickname"]
    avatar = res["avatar"]
    resp = make_response(jsonify({"status": True, "message": "%s welcome login" % nick_name}))
    resp.set_cookie("userId", user_id)
    # cookie不能存储中文
    resp.set_cookie("nickname", quote(nick_name, encoding="utf-8"))
    resp.set_cookie("avatar", avatar)
    log.info(f"Guest login success, {nick_name}")
    return resp


# 退出登录逻辑
@app.route("/mashang/loginOut/userInfo/<path:temp_user_id>", methods=["GET", "POST"])
def get_cookie(temp_user_id):
    """
        退出登录
    """
    # 后端改写保活状态
    try:
        sql = f"update sessiontable set isActive=0 where tempUserId='{temp_user_id}'"
        write_func(sql)
        log.info(f"Guest loginOut success, {temp_user_id}")
        return jsonify({"status": True, "message": "loginOut success"})
    except Exception as e:
        log.error(f"loginOut failed:\n{e}")
        return jsonify({"status": True, "message": "loginOut failed"})


# 文件上传，返回：{"status": True, "fileUrl": ""}
@app.route('/<re("index|fileUpload"):url>', methods=["GET", "POST"])
def upload(url):
    # 来源地址
    ip = request.remote_addr
    if request.method == "POST":
        # 判断是否登录
        token = request.headers.get("token")
        f = request.files["file"]
        sql = f"select * from sessiontable where tempUserId='{token}' and isActive=1;"
        if not token or not query_func(sql):
            # 未登录，文件放在common文件夹下
            save_path = os.path.join(BASIC_PATH, "common")
            file_url = f"http://{HOST}:{PORT}/download/common/{f.filename}" if VENV == "local" else \
                f"http://{HOST}/download/common/{f.filename}"
        else:
            # 已登录，文件放在userId文件夹下
            res = query_func(sql)
            user_id = res["userId"]
            save_path = os.path.join(BASIC_PATH, user_id)
            file_url = f"http://{HOST}:{PORT}/download/{user_id}/{f.filename}" if VENV == "local" else \
                f"http://{HOST}/download/{user_id}/{f.filename}"
        os.mkdir(save_path) if not os.path.exists(save_path) else save_path
        upload_path = os.path.join(save_path, f.filename)
        f.save(upload_path)
        # 埋入日志
        log.info(f"upload file_url {file_url} by {ip}")
        return jsonify({"status": True, "message": file_url})
    # 埋入日志
    log.info(f"request index page by {ip}")
    return render_template("fileServer.html")


# 文件下载
@app.route("/download/<path:dirname>/<path:filename>")
def download(dirname, filename):
    # 来源地址
    ip = request.remote_addr
    # 判断文件是否存在
    save_path = os.path.join(BASIC_PATH, dirname)
    if os.path.isdir(save_path) and filename in os.listdir(save_path):
        # 埋入日志
        log.info(f"download filename {filename} by {ip}")
        return send_from_directory(save_path, filename, as_attachment=True)
    # 埋入日志
    log.warning(f"download filename {filename} by {ip} is failed")
    return jsonify({"status": False, "message": "the filename is not exists"})


##############################################################################
# 文件详情
@app.route('/<re("fileDetail|fileDate"):url>', methods=["GET"])
def detail(url):
    # 来源地址
    ip = request.remote_addr
    if url == "fileDate":
        filenames = os.listdir(BASIC_PATH)
        files = [os.path.join(BASIC_PATH, item) for item in filenames]
        file_list = []
        for file in files:
            file_date = os.path.getmtime(file)
            file_name = os.path.basename(file)
            file_size = os.path.getsize(file)
            file_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_date))
            if VENV == "local":
                file_url = f"http://{HOST}:{PORT}/download/{file_name}"
            else:
                file_url = f"http://{HOST}/download/{file_name}"
            file_list.append(
                {"fileSize": file_size, "fileDate": file_date, "fileName": file_name, "fileUrl": file_url})
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
        if filename in os.listdir(BASIC_PATH):
            os.remove(os.path.join(BASIC_PATH, filename))
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
    filenames = os.listdir(BASIC_PATH)
    # {"文件名": "时间", ...}
    file_map = {os.path.join(BASIC_PATH, item): time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
        os.path.getmtime(os.path.join(BASIC_PATH, item)))) for item in filenames}
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
    # clean_file_handle()
    app.run(host=host, port=PORT, debug=False, use_reloader=False)
