var t;
var userId;
var nickname;
// 激活选择文件
const uploadFunc = () => {
    document.querySelector("#file").click();
}
// 拖拽文件上传
$(function () {
    // 阻止浏览器默认行为
    $(document).on({
        // 拖离
        dragleave: function (e) {
            e.preventDefault();
        },
        // 拖放后
        drop: function (e) {
            e.preventDefault();
        },
        // 拖进
        dragenter: function (e) {
            e.preventDefault();
        },
        // 拖来拖去
        dragover: function (e) {
            e.preventDefault();
        }
    });
    // 拖拽区域
    var box = document.getElementsByTagName("body")[0];
    box.addEventListener("drop", function (e) {
        // 取消默认浏览器拖拽效果
        e.preventDefault();
        // 获取文件对象
        var fileList = e.dataTransfer.files;
        var file = fileList[0];
        // 文件上传处理
        fileHandle(file);
        // 设置焦点
        $("#agree-btn").focus();
        // 清除拖拽文件
        e.dataTransfer.clearData();
    }, false)
})
// 绑定粘贴事件
function bindPaste(){
    // 粘贴区域
    var box = document.getElementsByTagName("body")[0];
    // 定义body标签绑定的事件函数
    var fun = function (e) {
        // 获取clipboardData对象
        var data = e.clipboardData || window.clipboardData;
        // 获取文件对象
        var file = data.items[0].getAsFile();
        // 判断文件是否存在
        if (file) {
            // 文件上传处理
            fileHandle(file);
        }
    }
    // 通过body标签绑定粘贴事件
    box.removeEventListener("paste", fun);
    box.addEventListener("paste", fun);
} 
// 选择文件上传
const uploadFile = async () => {
    // 获取文件列表对象
    var file = document.querySelector("#file").files[0];
    // 文件上传处理
    fileHandle(file);
    // 清空文件选择
    var elem = document.querySelector("#file");
    elem.outerHTML = elem.outerHTML;
}
// 文件上传处理
const fileHandle = (file) => {
    var fileName = file.name;
    var fileSzie = file.size;
    if (fileSzie > 1024 * 1024 * 20) {
        window.alert("文件大小不能超过20M!")
    } else {
        // 释放加载动画
        document.querySelector(".Loading").setAttribute("style", "display: block;");
        // 实例化一个表单数据对象
        var formData = new FormData();
        formData.append("file", file);
        // ajax请求
        var xhr = new XMLHttpRequest();
        // 回调处理
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    var res = xhr.responseText;
                    var status = JSON.parse(res).status;
                    var fileUrl = JSON.parse(res).file_url;
                    // 传送成功
                    if (status) {
                        // 显示提示框
                        document.querySelector("#popup").setAttribute("style", "display: block;");
                        // 设置文件链接
                        document.querySelector("#fileUrl").value = fileUrl;
                    } else {
                        window.alert(`${fileName}：上传失败，上传服务当前不可用！`)
                    }
                }
                // 加载完成
                document.querySelector(".Loading").setAttribute("style", "display: none;");
            }
        }
        // post请求发送表单数据
        xhr.open('POST', '/fileUpload', true);
        // 是否存在jwtToken
        if (localStorage.getItem("jwtToken")) {
            let jwtToken = localStorage.getItem("jwtToken");
            xhr.setRequestHeader("jwtToken", jwtToken);
        }
        // 发送请求
        xhr.send(formData);
    }
}
// fileUrl复制
const linkCopy = () => {
    // 移除disabled属性
    document.querySelector("#fileUrl").removeAttribute("disabled")
    // 复制到剪切板
    var input = document.getElementById("fileUrl")
    var text = input.value
    input.select();
    input.setSelectionRange(0, text.length);
    document.execCommand('copy');
    // 添加disabled属性
    document.querySelector("#fileUrl").setAttribute("disabled", "");
    // 提示框消失
    document.querySelector("#popup").setAttribute("style", "display: none;");
}
// 判断是否登录
const isLoginCheck = () => {
    // 是否存在jwtToken
    if (localStorage.getItem("jwtToken")) {
        // 获取用户信息
        $.ajax({
            url: "/mashang/user/userinfo",
            type: "get",
            headers: {
                "authorization": localStorage.getItem("jwtToken")
            },
            success: function(resp) {
                // 登录后的处理
                if (resp.status) {
                    // 获取payload
                    let payload = resp.payload;
                    let avatar = payload.avatar;
                    nickname = payload.nick_name;
                    userId = payload.user_id;
                    // 隐藏原有图标
                    $(".logo-box").hide();
                    // 显示用户信息 
                    $(".userInfo").css('display', 'block');
                    // 更新用户图标
                    $("#avatar").attr('src', avatar);
                    // 显示用户名称
                    $("#nickName").html("欢迎你，" + nickname);
                } else {
                    // 二维码展示
                    showQRcode();
                    // 展示初始动态图像
                    let pictureElement = $('<picture class="logo-box"><img src="../static/icon.gif" alt="" draggable="false"></picture>');
                    $("#user").before(pictureElement);
                }
            }
        })
    } else {
        // 二维码展示
        showQRcode();
        // 展示初始动态图像
        let pictureElement = $('<picture class="logo-box"><img src="../static/icon.gif" alt="" draggable="false"></picture>');
        $("#user").before(pictureElement);
    }
}
// 二维码展示
function showQRcode() {
    $.get("/mashang/login/qrCodeReturnUrl", function (result) {
        var qrcodeUrl = result.qrcode_url;
        var tempUserId = qrcodeUrl.split("=")[1];
        // 打印tempUserId
        console.log(tempUserId);
        localStorage.setItem("tempUserId", tempUserId);
        $("#loginQR").html("").qrcode({
            render: "canvas",
            width: 150,
            height: 150,
            foreground: "#0099ff",
            background: "#f9f9f9",
            text: encodeURI(qrcodeUrl),
        })
    })
}
// 登录处理（点击时触发）
const isLoginHandle = () => {
    if (userId) {
        // 携带jwtToken跳转
        window.location.href = `/${userId}/fileDetail?jwtToken=${localStorage.get(jwtToken)}`;
    } else {
        // 展示wx登录界面
        $("#loginWrap").css("display", "block");
        // 监听客户是否扫码登录
        t = window.setInterval(function () {
            // ajax请求
            let url = "/mashang/user/token?tempUserId="+ localStorage.getItem("tempUserId");
            $.get(url, function (resp) {
                if (resp.status) {
                    // 存储jwtToken
                    let jwtToken = resp.jwt_token;
                    localStorage.setItem("jwtToken", jwtToken);
                    // 取消定时
                    window.clearTimeout(t)
                    // 调用用户信息接口
                    $.ajax({
                        url: "/mashang/user/userinfo",
                        type: "get",
                        headers: {
                            "authorization": jwtToken
                        },
                        success: function(resp) {
                            // 登录后的处理
                            if (resp.status) {
                                // 获取payload
                                let payload = resp.payload;
                                let avatar = payload.avatar;
                                nickname = payload.nick_name;
                                // 关闭扫码登录界面
                                $("#loginWrap").css("display", "none");
                                // 隐藏原有图标
                                $(".logo-box").hide();
                                // 显示用户信息 
                                $(".userInfo").css('display', 'block');
                                // 更新用户图标
                                $("#avatar").attr('src', avatar);
                                // 显示用户名称
                                $("#nickName").html("欢迎你，" + nickname);
                            }
                        }        
                    })
                }
            })
        }, 1000)
    }
}
// 退出登录
function logout() {
    // 调退出登录接口
    $.ajax({
        url: "/mashang/user/logout",
        type: "post",
        headers: {
            "authorization": localStorage.getItem("jwtToken")
        },
        success: function(resp) {
            if (resp.status) {
                // 清除浏览器存储
                localStorage.clear();
            }
        }
    })
}
// 页面加载完成
window.onload = function () {
    // 剪切监听
    bindPaste();
    // 登录校验
    isLoginCheck();
    // 关闭微信登录界面1
    $("#loginClose").on("click", function () {
        // 取消二维码显示
        $("#loginWrap").css("display", "none");
        // 取消定时
        window.clearTimeout(t)
    });
    // 关闭微信登录界面2
    $("#loginMask").on("click", function() {
        // 取消二维码显示
        $("#loginWrap").css("display", "none");
        // 取消定时
        window.clearTimeout(t)
    })
    // nickname绑定鼠标移动事件
    $(".user .userName").mouseover(function () {
        $(".userName").css("color", "#000000");
        $("#nickName").html("退出登录");
    });
    $(".user .userName").mouseout(function () {
        $(".userName").css("color", "#4191f5");
        $("#nickName").html("欢迎你，" + nickname);
    });
    // 监听点击退出登录
    $(".user .userName").on("click", function () {
        // 退出登录
        logout();
        // 刷新当前页
        window.location.reload();
    });
}