let wsUrl = 'wss://server01.vicy.cn/8lXdSX7FSMykbl9nFDWESdc6zfouSAEz/wxlogin/webSocket';
let baseUrl = "https://server01.vicy.cn/8lXdSX7FSMykbl9nFDWESdc6zfouSAEz/wxlogin";
let webSocket;
let token;
(function () {
  // 判断是否已经登录
  isLogin();
  let loginModal =
    '<div class="loginWrap" id="loginWrap">\n' +
    '  <div id="loginMask" class="loginMask"></div>\n' +
    '  <div class="loginCol">\n' +
    '    <div class="title">\n' +
    "      <span>扫码登录</span>\n" +
    '      <div id="loginClose" class="loginClose"><img class="icon" src="./static/image/close.png" /></div>\n' +
    "    </div>\n" +
    '    <div class="loginMain">\n' +
    '      <div class="loginQR" id="loginQR"></div>\n' +
    '      <div class="tips">请使用微信扫码登录</div>\n' +
    "    </div>\n" +
    "  </div>\n" +
    "</div>";
  $("body").append(loginModal);
})();

$(".topLeft").click(function () {
  window.location.href = 'index.html';
})

$("#wxLogin").click(function () {
  openLogin();
})

function openLogin() {
  webSocket = new WebSocket(wsUrl);
  webSocket.onopen = socketOpen;
  webSocket.onmessage = socketMessage;
  webSocket.onerror = onError;
  webSocket.onclose = onClose;
  $("#loginWrap").fadeIn(500);
}

function socketOpen(e) {
  console.log("socketOpen", e);
  webSocket.send("qrCodeInfo");
}

function socketMessage(e) {
  let msgData = JSON.parse(e.data);
  console.log("socketMessage", e, msgData);
  if (msgData.type == "wxLogin") {
    getQrCode(msgData.content);
  }
  if (msgData.type == "loginSuccess") {
    $.myToast("登录成功");
    localStorage.setItem("userInfo", JSON.stringify(msgData.content));
    isLogin();
    $("#loginClose").click();
    setTimeout(() => {
      window.location.href = 'user.html';
    }, 800);
  }
}

function onClose(e) {
  console.log("onClose", e);
  webSocket = null;
}

function onError(e) {
  console.log("onError", e);
}

$("#loginClose,#loginMask").on("click", function () {
  $("#loginWrap").fadeOut(500);
  webSocket.close();
});

function getQrCode(msg) {
  // $("#loginQR");
  $("#loginQR").html("").qrcode({
    render: "canvas", //也可以替换为table
    width: 150,
    height: 150,
    foreground: "#0099ff",
    background: "#f9f9f9",
    text: encodeURI(msg),
  });
}

function isLogin() {
  if (localStorage.getItem("userInfo")) {
    let user = JSON.parse(localStorage.getItem("userInfo"));
    token = user.token;

    $(".userInfo").css('display', 'flex');
    $("#avatar").attr('src', user.user.avatar);
    $("#nickName").html(user.user.nickname);
    $(".wxLogin").hide();
  } else {
    token = "";

    $(".userInfo").hide();
    $(".wxLogin").css('display', 'flex');
  }
}

$("#logout").click(function () {
  localStorage.removeItem("userInfo");
  token = "";
  window.location.href = "index.html";
});

$("#user").click(function () {
  window.location.href = 'user.html'
})


/**
 * @description: 防抖
 * @param {fn:function,wait:number,immediate}
 * @return {type}
 */
var debounce = (fn, wait, immediate = false) => {
  let timer,
    startTimeStamp = 0;
  let context, args;

  let run = (timerInterval) => {
    timer = setTimeout(() => {
      let now = new Date().getTime();
      let interval = now - startTimeStamp;
      if (interval < timerInterval) {
        // the timer start time has been reset，so the interval is less than timerInterval
        console.log("debounce reset", timerInterval - interval);
        startTimeStamp = now;
        run(wait - interval); // reset timer for left time
      } else {
        if (!immediate) {
          fn.apply(context, args);
        }
        clearTimeout(timer);
        timer = null;
      }
    }, timerInterval);
  };

  return function () {
    context = this;
    args = arguments;
    let now = new Date().getTime();
    startTimeStamp = now; // set timer start time

    if (!timer) {
      console.log("debounce set", wait);
      if (immediate) {
        fn.apply(context, args);
      }
      run(wait);
    }
  };
};

/**
 * @description: 封装get请求
 * @param {url:string,data:object}
 * @return {Promise}
 */
function myGet(url, data) {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: baseUrl + url,
      type: "get",
      headers: {
        Authentication: token,
      },
      username: 0,
      password: 0,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-MicrosoftAjax", "Delta=true");
      },
      contentType: "application/x-www-form-urlencoded",
      data: data,
      success: (res) => {
        resolve(res);
      },
      error: (err) => {
        if (err.status == 401) {
          // 跳转到登录
          if (window.location.href.includes("/user.html")) {
            $.myToast("登录已过期");
            localStorage.removeItem("userInfo");
            setTimeout(() => {
              window.location.href = "index.html";
            }, 800);
            return;
          }
          if (token) {
            $.myToast("登录已过期");
            localStorage.removeItem("userInfo");
            token = "";
            isLogin()
          }
          openLogin();
        } else {
          reject(err);
        }
      },
    });
  });
}

/**
 * @description: 封装post请求
 * @param {url:string,data:object}
 * @return {Promise}
 */
function myPost(url, data) {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: baseUrl + url,
      type: "post",
      username: 0,
      password: 0,
      headers: {
        Authentication: token,
      },
      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-MicrosoftAjax", "Delta=true");
      },
      contentType: "application/x-www-form-urlencoded",
      data: data,
      success: (res) => {
        resolve(res);
      },
      error: (err) => {
        if (err.status == 401) {
          // 跳转到登录
          if (window.location.href.includes("/user.html")) {
            $.myToast("登录已过期");
            localStorage.removeItem("userInfo");
            setTimeout(() => {
              window.location.href = "index.html";
            }, 800);
            return;
          }
          if (token) {
            $.myToast("登录已过期");
            localStorage.removeItem("userInfo");
            token = "";
            isLogin()
          }
          openLogin();
        } else {
          reject(err);
        }
      },
    });
  });
}