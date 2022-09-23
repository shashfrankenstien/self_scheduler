import os
import re
from datetime import datetime as dt

from .base import DB
from .project import Project



def email_format_ok(email):
    return re.match(r".*\@.*\..*", email) != None

class LoginError(Exception):
    pass


class SelfSchedulerDB(DB):

    def __init__(self, workspace_path) -> None:
        db_path = os.path.join(workspace_path, "inventory.db")
        super().__init__(db_path)
        self.workspace_path = workspace_path


    def create_tables(self):
        conn = self.get_connection()

        # self.execute('''CREATE DATABASE IF NOT EXISTS self_scheduler;''', conn=conn)
        self.execute('''PRAGMA foreign_keys=ON;''')
        self.execute('''PRAGMA journal_mode=WAL;''')

        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT DEFAULT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                create_dt TEXT NOT NULL
            )
        ''', conn=conn)

        self.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                create_dt TEXT NOT NULL,
                sched_every TEXT DEFAULT NULL,
                sched_at TEXT DEFAULT NULL,
                last_run_dt TEXT DEFAULT NULL,
                last_run_res TEXT DEFAULT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''', conn=conn)


    def user_exists(self, email):
        if not email_format_ok(email):
            raise Exception("Invalid email")

        res = self.execute(f'''SELECT email FROM users WHERE email = '{email}' ''', fetch_one=True)
        return res is not None


    def get_user(self, email):
        u = self.execute(f'''SELECT * FROM users WHERE email = '{email}' ''', fetch_one=True)
        if u is None:
            raise LoginError("Incorrect credentials")
        return User(self.workspace_path, self.db_path, u.id, u.first_name, u.last_name, u.email, u.salt)


    def login_user(self, email, password):
        u = self.execute(f'''SELECT * FROM users WHERE email = '{email}' ''', fetch_one=True)
        if u is None:
            raise LoginError("Incorrect credentials")
        passhash = self.hash_password(password=password, salt=u.salt)
        if u.password != passhash:
            raise LoginError("Incorrect credentials")
        return User(self.workspace_path, self.db_path, u.id, u.first_name, u.last_name, u.email, u.salt)


    def create_new_user(self, first_name, last_name, email, password):
        if self.user_exists(email):
            raise Exception("User already exists")

        salt = self.create_salt()
        passhash = self.hash_password(password=password, salt=salt)
        self.execute(f'''
            INSERT INTO users (
                first_name, last_name, email,
                password, salt, create_dt
            )
            VALUES (
                '{first_name}', '{last_name}', '{email}',
                '{passhash}', '{salt}',
                '{dt.now().strftime('%Y-%m-%d %H:%M:%S')}'
            );
        ''')

        return self.get_user(email)





class User(DB):

    def __init__(self, workspace_path, db_path, user_id, first_name, last_name, email, salt):
        super().__init__(db_path)
        self.workspace_path = workspace_path
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.salt = salt


    def project_exists(self, name):
        res = self.execute(f'''
            SELECT project_id FROM projects WHERE user_id = {self.user_id} AND name = '{name}'
        ''', fetch_one=True)
        return res is not None


    def get_project(self, name):
        res = self.execute(f'''SELECT id FROM projects WHERE user_id = {self.user_id} AND name = '{name}' ''', fetch_one=True)
        if res is None:
            raise Exception("Project not found")

        return Project(self.workspace_path, self.db_path, self, res.id, name)


    def create_new_project(self, name):
        if self.project_exists(name):
            raise Exception("Project already exists")

        self.execute(f'''
            INSERT INTO projects (
                user_id, name, create_dt
            )
            VALUES (
                '{self.user_id}', '{name}',
                '{dt.now().strftime('%Y-%m-%d %H:%M:%S')}'
            );
        ''')

        return self.get_project(name)



# SHOW FUNCTION STATUS
# WHERE db = "self_scheduler"

# SHOW TABLES FROM self_scheduler
# SHOW FULL TABLES IN self_scheduler

# create function if not exists self_scheduler.PASS_HASH(pass VARCHAR(100), salt VARCHAR(100))
# RETURNS TEXT DETERMINISTIC
# RETURN SHA2(CONCAT(salt, pass, salt), 256) ;
