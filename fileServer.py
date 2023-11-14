import os
import jwt
import json
import time
import socket
import requests

from threading import Timer
from urllib import request as rq
from jwt import ExpiredSignatureError
from utils.logServer import blance_logging
from werkzeug.routing import BaseConverter
from flask import Flask, render_template, request, jsonify, send_from_directory
from utils.algorithm import mine_decrypt, generate_jwt_token, jwt_secret_key, \
    jwt_algorithm, remove_key_by_value


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
# 存储用户信息字典
session_dict = {}
# 当前环境
VENV = "prod"  # TODO 环境切换时：local or prod
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
    log.info(f"Get qrcode_url {qrcode_url} success")
    return jsonify({"qrcode_url": qrcode_url})


# 回调接口，存储JWT令牌
@app.route("/mashang/login/callback", methods=["POST"])
def callback():
    user_id = request.form.get("userId")
    temp_user_id = request.form.get("tempUserId")
    nick_name = request.form.get("nickname", "Guest")
    avatar = request.form.get("avatar", "https://thirdwx.qlogo.cn/mmopen/vi_32/Q3auHgzwzM6npDo4Vgk61VOvQ"
                                        "da0pAh3ccfZyT6A6rW86ciaiaiaNjdQD9LN9xyxhNJLyu7cnUdL0gWdsPGccNcoQ/132")
    ip_addr = request.form.get("ipAddr")
    payload = {"user_id": user_id, "nick_name": nick_name, "avatar": avatar, "ip_addr": ip_addr}
    jwt_token = generate_jwt_token(payload)
    # 签发jwt_token
    session_dict.update({temp_user_id: jwt_token})
    log.info(f"generate jwt token {jwt_token} success")
    return jsonify({"status": True, "errcode": 0})


# 获取登录的JWT
@app.route("/mashang/user/token", methods=["GET"])
def get_token():
    temp_user_id = request.args.get("tempUserId", None)
    if not temp_user_id or temp_user_id not in session_dict:
        return jsonify({"status": False, "message": "please scan weixin QRcode", "jwt_token": ""})
    jwt_token = session_dict["temp_user_id"]
    log.info(f"get jwt token success, {temp_user_id}")
    return jsonify({"status": True, "jwt_token": jwt_token, "message": "success"})


def get_jwt_token_and_payload():
    jwt_token = request.headers.get("authorization")
    try:
        payload = jwt.decode(jwt_token, jwt_secret_key, algorithms=jwt_algorithm)
    except ExpiredSignatureError:
        # 维护session_dict
        remove_key_by_value(jwt_token, session_dict)
        return jsonify({"status": False, "message": "the jwtToken has expired"})
    except Exception as e:
        print(e)
        return jsonify({"status": False, "message": "the jwtToken is illegality"})
    return jwt_token, payload


def login_check(func):
    def wrapper(*args, **kwargs):
        jwt_token, payload = get_jwt_token_and_payload()
        # 回写request
        request.payload = payload
        # 是否退出登录
        if "logout" in request.url:
            # 维护session_dict
            remove_key_by_value(jwt_token, session_dict)

        return func(*args, **kwargs)

    return wrapper


# 登录结果响应
@login_check
@app.route("/mashang/user/userinfo", methods=["GET"])
def userinfo():
    # 获取payload
    payload = request.payload
    nick_name = payload["nick_name"]
    # 设置响应
    log.info(f"Guest {nick_name}, is login")
    return jsonify({"status": True, "payload": payload, "message": "success"})


# 退出登录逻辑
@login_check
@app.route("/mashang/user/logout", methods=["POST"])
def logout():
    """
        退出登录
    """
    # 获取payload
    payload = request.payload
    nick_name = payload["nick_name"]
    log.info(f"Guest {nick_name}, loginOut success")
    return jsonify({"status": True, "message": "logout success"})


# 文件上传，返回：{"status": True, "fileUrl": ""}
@app.route('/<re("index|fileUpload"):url>', methods=["GET", "POST"])
def upload(url):
    # 来源地址
    ip = request.remote_addr
    if request.method == "POST":
        # 判断是否登录
        try:
            _, payload = get_jwt_token_and_payload()
            f = request.files["file"]
            # 已登录，文件放在userId文件夹下
            user_id = payload["user_id"]
            save_path = os.path.join(BASIC_PATH, user_id)
            file_url = f"http://{HOST}:{PORT}/download/{user_id}/{f.filename}" if VENV == "local" else \
                f"http://{HOST}/download/{user_id}/{f.filename}"
        except Exception as e:
            print(e)
            # 未登录
            f = request.files["file"]
            save_path = os.path.join(BASIC_PATH, "common")
            file_url = f"http://{HOST}:{PORT}/download/common/{f.filename}" if VENV == "local" else \
                f"http://{HOST}/download/common/{f.filename}"
        os.mkdir(save_path) if not os.path.exists(save_path) else save_path
        upload_path = os.path.join(save_path, f.filename)
        f.save(upload_path)
        # 埋入日志
        log.info(f"upload file_url {file_url} by {ip}")
        return jsonify({"status": True, "file_url": file_url, "message": "success"})
    # 埋入日志
    log.info(f"request index page by {ip}")
    return render_template("fileServer.html")


# 文件下载--不用判断是否登录
@app.route("/download/<path:dirname>/<path:filename>", method=["GET"])
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


# 文件详情页面
@app.route("/<path:user_id>/fileDetail", methods=["GET"])
def detail(user_id):
    jwt_token = request.args.get("jwtToken", None)
    try:
        payload = jwt.decode(jwt_token, jwt_secret_key, algorithms=jwt_algorithm)
    except ExpiredSignatureError:
        # 维护session_dict
        remove_key_by_value(jwt_token, session_dict)
        return jsonify({"status": False, "message": "the jwtToken has expired"})
    except Exception as e:
        print(e)
        return jsonify({"status": False, "message": "the jwtToken is illegality"})
    # user_id校验
    payload_user_id = payload["user_id"]
    if user_id != payload_user_id:
        return jsonify({"status": False, "message": "the user_id is illegality"})
    # 请求用户
    log.info(f"request fileDetail page by {user_id}")
    return render_template("fileDetail.html")


# 文件详情信息
@login_check
@app.route('/<path:user_id>/fileData', methods=["GET"])
def detail(user_id):
    # 来源地址
    ip = request.remote_addr
    save_path = os.path.join(BASIC_PATH, user_id)
    os.mkdir(save_path) if not os.path.exists(save_path) else save_path
    filenames = os.listdir(save_path)
    files = [os.path.join(save_path, item) for item in filenames]
    file_list = []
    for file in files:
        file_date = os.path.getmtime(file)
        file_name = os.path.basename(file)
        file_size = os.path.getsize(file)
        file_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_date))
        if VENV == "local":
            file_url = f"http://{HOST}:{PORT}/download/{user_id}/{file_name}"
        else:
            file_url = f"http://{HOST}/download/{user_id}/{file_name}"
        file_list.append(
            {"fileSize": file_size, "fileDate": file_date, "fileName": file_name, "fileUrl": file_url})
    # 按日期倒序
    file_list = sorted(file_list, key=lambda item: item["fileDate"], reverse=True)
    # 转json格式，支持中文
    file_list = json.dumps(file_list, ensure_ascii=False)
    # 埋入日志
    log.info(f"request size {len(file_list)}b by {ip}")
    return jsonify({"status": True, "message": file_list})


# 文件删除接口
@login_check
@app.route('/<path:user_id>/fileDel/<path:filename>', methods=["DELETE"])
def delete(user_id, filename):
    # 来源地址
    ip = request.remote_addr
    save_path = os.path.join(BASIC_PATH, user_id)
    os.mkdir(save_path) if not os.path.exists(save_path) else save_path
    filenames = os.listdir(save_path)
    try:
        if filename in filenames:
            os.remove(os.path.join(save_path, filename))
            # 埋入日志
            log.warning(f"{user_id} delete file {filename} by {ip}")
            return jsonify({"status": True, "message": "delete success"})
        # 埋入日志
        log.warning(f"{user_id} delete filename {filename} by {ip} is failed")
        return jsonify({"status": False, "message": f"the filename is not exists"})
    except Exception as e:
        log.error(f"{user_id} delete filename {filename} by {ip} is error")
        return jsonify({"status": False, "message": f"the filename delete failed: {e}"})


# 404.html
@app.errorhandler(404)
def miss(e):
    log.warning(f"request 404 page by {request.remote_addr}")
    return render_template("404.html"), 404


# 文件定时清理
def file_remove_handle():
    """
        清理规则：
        公共文件夹每个文件保留30分钟
        用户文件夹最多存储100个文件
    """
    dirs = os.listdir(BASIC_PATH)
    now = time.time()
    for dir_ in dirs:
        path = os.path.join(BASIC_PATH, dir_)
        if os.path.isdir(path):
            inner_files = [os.path.join(path, item) for item in os.listdir(path)]
            if dir_ == "common":
                for inner_file in inner_files:
                    file_date = os.path.getmtime(inner_file)
                    if now - file_date > 1800:
                        try:
                            os.remove(inner_file)
                            log.info(f"delete {inner_file} success")
                        except Exception as e:
                            print(e)
                            log.error(f"delete {inner_file} failed * {e}")
                            continue
            else:
                if len(os.listdir(path)) > 100:
                    file_map = {inner_file: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                        os.path.getmtime(inner_file))) for inner_file in inner_files}
                    # 按时间倒序排列文件
                    file_list = sorted(file_map, key=lambda item: file_map[item], reverse=True)
                    # 待清理的文件列表
                    clean_file_list = file_list[100:]
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
    """
        5分钟定时跑一次
    """
    log.info(f"start clean server file...")
    file_remove_handle()
    t = Timer(function=clean_file_handle, interval=300)
    t.start()


# 定时任务放在main外面
clean_file_handle()

if __name__ == '__main__':
    app.run(host=host, port=PORT, debug=False, use_reloader=False)
