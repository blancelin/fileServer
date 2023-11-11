"""
    一些常用的算法
"""
import jwt
import time
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from Crypto.Util.Padding import pad, unpad

KEY = "236278602rpa6666"  # 盐
BLOCK_SIZE = 32  # 补充位数
# 配置JWT密钥和算法
jwt_secret_key = "blance"
jwt_algorithm = "HS256"


def mine_encrypt(string):
    """
        AES16位加密算法
    :param string: 待加密字符
    :return: 16位加密字符
    """

    length = 16
    count = len(string)
    if count % length != 0:
        add = length - (count % length)
    else:
        add = 0
    string = (string + ("\0" * add)).encode()
    crypto_inst = AES.new(KEY.encode(), AES.MODE_ECB)
    crypto_text = crypto_inst.encrypt(pad(string, BLOCK_SIZE))
    encrypt_string = b2a_hex(crypto_text).upper().decode()

    return encrypt_string


def mine_decrypt(string):
    """
        AES16位解密算法
    :param string: 待解密字符
    :return: 解密字符
    """
    crypto_inst = AES.new(KEY.encode(), AES.MODE_ECB)
    crypto_text = unpad(crypto_inst.decrypt(a2b_hex(string)), BLOCK_SIZE)

    return crypto_text.decode().rstrip('\0')


# 生成JWT令牌
def generate_jwt_token(payload, exp=3600 * 24):
    key = jwt_secret_key
    now = time.time()
    payload = payload.update({"exp": now + exp})
    return jwt.encode(payload, key, algorithm=jwt_algorithm)


if __name__ == '__main__':
    print("加密：{0}".format(mine_encrypt("hello world")))
    print("解密：{0}".format(mine_decrypt(mine_encrypt("hello world"))))
