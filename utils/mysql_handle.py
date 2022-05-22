import pymysql
from pymysql.cursors import DictCursor

from utils.algorithm import mine_decrypt


class MysqlHandle:
    def __init__(self):
        self.conn, self.cursor = self.connect()

    @staticmethod
    def connect():
        encrypt_pwd = "D358935695ED180982FF75E23D6BD24FAADFB4EF8980227D9CD2727685E1DAB5"
        conn = pymysql.connect(
            user="root",
            password=mine_decrypt(encrypt_pwd),
            host="127.0.0.1",
            port=3306,
            db="sample",
            cursorclass=DictCursor
        )
        cursor = conn.cursor()
        return conn, cursor

    def write_op(self, sql):
        self.cursor.execute(sql)
        self.conn.commit()

    def query_op(self, sql, args=None):
        self.cursor.execute(sql, args)
        res = self.cursor.fetchone()
        return res

    def close_db(self):
        self.cursor.close()
        self.conn.close()


def write_func(sql):
    """
        写函数
    """
    mql = MysqlHandle()
    mql.write_op(sql)
    mql.close_db()


def query_func(sql, args=None):
    """
        查函数
    """
    mql = MysqlHandle()
    res = mql.query_op(sql, args)
    mql.close_db()
    return res
