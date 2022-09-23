import random
import hashlib

import sqlite3
from collections import namedtuple



def namedtuple_factory(cursor, row):
    fields = [col[0] for col in cursor.description]
    Row = namedtuple("Row", fields)
    return Row(*row)



class DB:

    def __init__(self, db_path) -> None:
        self.db_path = db_path


    def create_salt(self):
        return hashlib.sha256(str(random.random()).encode()).hexdigest()

    def hash_password(self, password, salt):
        return hashlib.sha256(f"{salt}{password}{salt}".encode()).hexdigest()



    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = namedtuple_factory
        return conn


    def execute(self, sql, conn=None, fetch_one=False, fetch_n=None):
        created_conn = False
        if conn is None:
            conn = self.get_connection()
            created_conn = True
        try:
            cur = conn.cursor()
            cur.execute(sql)
            if fetch_one is True:
                res = cur.fetchone()
            elif isinstance(fetch_n, int):
                res = cur.fetchmany(fetch_n)
            else:
                res = cur.fetchall()
            cur.close()
            return res
        except:
            print(sql)
            raise
        finally:
            if created_conn:
                conn.commit()
                conn.close()



