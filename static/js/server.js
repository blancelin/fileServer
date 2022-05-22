var isLogin;
var tempUserId;
var t;
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
        // 等待3s
        // await sleep(3000);
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
                    var fileUrl = JSON.parse(res).message;
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
// 登录处理（点击时触发）
const isLoginHandle = () => {
    if (isLogin) {
        // 根据userId跳转到详情页
        window.location.href = `/${localStorage.getItem("userId")}/fileDetail`;
    } else {
        // 展示wx登录界面
        $("#loginWrap").css("display", "block");
        // 监听客户是否扫码登录
        t = window.setInterval(function () {
            // ajax请求
            $.ajax({
                url: "/mashang/user/login",
                type: "get",
                headers: {
                    "token": tempUserId
                },
                success: function(resp) {
                    // 登录后的处理
                    if (resp.status) {
                        // 获取cookies
                        let userId = getCookie("userId");
                        let nickname = decodeURI(getCookie("nickname"));
                        let avatar = getCookie("avatar");
                        // 删除2个cookie，留下1个清空本地存储做判断
                        clearCookie("userId");
                        clearCookie("nickname");
                        // clearCookie("avatar");
                        // 浏览器会话存储
                        localStorage.setItem("userId", userId);
                        localStorage.setItem("nickname", nickname);
                        localStorage.setItem("avatar", avatar);
                        localStorage.setItem("token", tempUserId);
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
                        // 更改登录标识
                        isLogin = true;
                        // 取消定时
                        window.clearTimeout(t)
                    }
                }
            })
        }, 1000)
    }
}
// 判断是否登录
const isLoginCheck = () => {
    if (localStorage.getItem("userId")) {
        let nickname = localStorage.getItem("nickname");
        let avatar = localStorage.getItem("avatar");
        // 隐藏原有图标
        $(".logo-box").hide();
        // 显示用户信息 
        $(".userInfo").css('display', 'block');
        // 更新用户图标
        $("#avatar").attr('src', avatar);
        // 显示用户名称
        $("#nickName").html("欢迎你，" + nickname);
        // 更改登录标识
        isLogin = true;
    } else {
        // 二维码展示
        $.get("/mashang/login/qrCodeReturnUrl", function (result) {
            var qrcodeUrl = result.qrcode_url;
            tempUserId = qrcodeUrl.split("=")[1];
            // console.log(tempUserId);
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
}
// 页面加载完成
window.onload = function () {
    // 登录校验
    isLoginCheck();
    // 关闭wx登录界面
    $("#loginClose").on("click", function () {
        // 取消二维码显示
        $("#loginWrap").css("display", "none");
        // 取消定时
        window.clearTimeout(t)
    });
    // nickname绑定鼠标移动事件
    $(".user .userName").mouseover(function () {
        $(".userName").css("color", "#000000");
        $("#nickName").html("退出登录");
    });
    $(".user .userName").mouseout(function () {
        $(".userName").css("color", "#4191f5");
        $("#nickName").html("欢迎你，" + localStorage.getItem("nickname"));
    });
    // 监听点击退出登录
    $(".user .userName").on("click", function () {
        // 清除最后一个cookie
        clearCookie("avatar");
        // 刷新当前页
        window.location.reload();
    });
}
// 清空浏览器本地存储
if(!(getCookie("avatar"))) {
    // 当有本地存储时，调退出登录接口
    if (localStorage.length > 0) {
        // 调退出登录接口
        $.ajax({
            url: "/mashang/user/loginOut",
            type: "get",
            headers: {
                "token": localStorage.getItem("token")
            },
            success: function(resp) {
                console.log(resp);
            }
        })
    }
    localStorage.clear();
}
// 公共方法
// 设置cookie
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}
// 获取cookie
function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1);
        if (c.indexOf(name) != -1) return c.substring(name.length, c.length);
    }
    return "";
}
//清除cookie  
function clearCookie(name) {  
    setCookie(name, "", -1);  
}  
// 显示对象属性和方法
function dir(Obj) {
    var attributes = '';
    var methods = '';
    for (const attr in Obj) {
        if (Obj.attr != null)
            attributes = attributes + attr + ' 属性： ' + Obj.i + '\r\n';
        else
            methods = methods + '方法: ' + attr + '\r\n';
    }
    return attributes, methods
}
// sleep函数 await sleep(ms)进行调用;
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}