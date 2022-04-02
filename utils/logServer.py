# -*- coding:utf-8 -*-
import os
import logging
import colorlog

# 日志文件路径
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log")
# 设置控制台打印的颜色
colors_config = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'blue',
}


def blance_logging():
    # 实例化logger对象,需要加name，否则默认root会添加flask日志
    logger = logging.getLogger("blance")
    # 设置日志最低级别
    logger.setLevel(logging.DEBUG)
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        log_colors=colors_config)
    base_formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    # 输出到控制台
    sh = logging.StreamHandler()
    # 控制台格式
    sh.setFormatter(color_formatter)
    # 输出到日志文件
    fh = logging.FileHandler(log_path, encoding="utf-8")
    # 日志文件格式
    fh.setFormatter(base_formatter)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


if __name__ == '__main__':
    log = blance_logging()
    log.warning("request is illegal, please don't do that")

