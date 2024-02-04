import os
import re
import hashlib
from datetime import datetime as dt

from .base import DB
from .project import Project

from . import ss_sched


__SS_DB_SINGLETON = None

def get_ss_db_object(workspace_path):
    global __SS_DB_SINGLETON
    if __SS_DB_SINGLETON is None:
        __SS_DB_SINGLETON = SelfSchedulerDB(workspace_path)
    return __SS_DB_SINGLETON


def email_format_ok(email):
    return re.match(r".*\@.*\..*", email) != None

class LoginError(Exception):
    pass


# adding a custom function that will be triggered from SQL
DB.add_custom_function('sched_delete_job', 1, ss_sched.delete_job)


class SelfSchedulerDB(DB):

    def __init__(self, workspace_path) -> None:
        if not os.path.isdir(workspace_path):
            os.makedirs(workspace_path)
        db_path = os.path.join(workspace_path, "inventory.db")
        super().__init__(db_path)
        self.workspace_path = workspace_path
        self._create_tables()
        self._reload_jobs()


    def _create_tables(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT DEFAULT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                create_dt TEXT NOT NULL
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                name_hash TEXT NOT NULL,
                descr TEXT,
                create_dt TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS entry_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                file TEXT NOT NULL,
                func TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                create_dt TEXT NOT NULL,
                UNIQUE(project_id, file, func),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_id INTEGER NOT NULL,
                every TEXT DEFAULT NULL,
                at TEXT DEFAULT NULL,
                tzname TEXT DEFAULT NULL,
                is_scheduled INTEGER DEFAULT 0,
                last_run_dt TEXT DEFAULT NULL,
                last_run_res TEXT DEFAULT NULL,
                create_dt TEXT NOT NULL,
                UNIQUE(ep_id, every, at, tzname),
                FOREIGN KEY(ep_id) REFERENCES entry_points(id) ON DELETE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS sched_delete
            AFTER DELETE ON schedule
            BEGIN
                SELECT sched_delete_job(OLD.id);
            END;
        ''')

        conn.commit()
        conn.close()


    def _reload_jobs(self):
        res = self.execute('''SELECT DISTINCT email FROM users''')
        for r in res:
            if r.email is None:
                continue
            u = self.get_user(r.email)
            for p in u.get_all_projects():
                p.reload_schedules()


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
        if email == "" or password == "":
            raise ValueError("missing required fields")

        u = self.execute(f'''SELECT * FROM users WHERE email = '{email}' ''', fetch_one=True)
        if u is None:
            raise LoginError("Incorrect credentials")
        passhash = self.hash_password(password=password, salt=u.salt)
        if u.password != passhash:
            raise LoginError("Incorrect credentials")
        return User(self.workspace_path, self.db_path, u.id, u.first_name, u.last_name, u.email, u.salt)


    def create_new_user(self, first_name, last_name, email, password):
        if first_name == "" or last_name == "" or email == "" or password == "":
            raise ValueError("missing required fields")

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

        hashed = hashlib.md5(self.email.strip().lower().encode()).hexdigest()
        self.gravatar_url = f'https://www.gravatar.com/avatar/{hashed}?s=200&d=retro'


    def project_exists(self, name_hash):
        res = self.execute(f'''
            SELECT id FROM projects WHERE user_id = {self.user_id} AND name_hash = '{name_hash}'
        ''', fetch_one=True)
        return res is not None


    def get_projects_dict(self):
        projs = self.execute(f'''
        SELECT p.*,
        count(ep.id) AS entry_points,
        count(sch.id) AS schedules,
        sum(sch.is_scheduled) AS schedules_enabled
        FROM projects p
        LEFT JOIN entry_points ep
            ON ep.project_id = p.id
        LEFT JOIN schedule sch
            ON sch.ep_id = ep.id
        WHERE p.user_id = {self.user_id}
        GROUP BY p.id
        ''')
        return [proj._asdict() for proj in projs]


    def get_project(self, name_hash):
        res = self.execute(f'''SELECT id, name, descr FROM projects WHERE user_id = {self.user_id} AND name_hash = '{name_hash}' ''', fetch_one=True)
        if res is None:
            raise Exception("Project not found")
        return Project(self.workspace_path, self.db_path, self, res.id, res.name, name_hash, res.descr)


    def get_all_projects(self):
        projects = []
        res = self.execute(f'''SELECT * FROM projects WHERE user_id = {self.user_id}''')
        for r in res:
            if r.id is None:
                continue
            p = Project(self.workspace_path, self.db_path, self, r.id, r.name, r.name_hash, r.descr)
            projects.append(p)
        return projects


    def create_new_project(self, name, descr):
        name = str(name).strip()
        if name == "":
            raise ValueError("project name cannot be empty")

        name_hash = hashlib.md5(str(name).strip().encode()).hexdigest()

        if self.project_exists(name_hash):
            raise Exception("Project already exists")

        descr = descr.replace("'", "''")
        self.execute(f'''
            INSERT INTO projects (
                user_id, name, name_hash, descr, create_dt
            )
            VALUES (
                '{self.user_id}', '{name}', '{name_hash}', '{descr}',
                '{dt.now().strftime('%Y-%m-%d %H:%M:%S')}'
            );
        ''')

        P = self.get_project(name_hash)
        P.create_default_files() # only create default files the first time a project is created
        P.create_default_entry_point() # only create default entry point the first time a project is created
        return P



# SHOW FUNCTION STATUS
# WHERE db = "self_scheduler"

# SHOW TABLES FROM self_scheduler
# SHOW FULL TABLES IN self_scheduler

# create function if not exists self_scheduler.PASS_HASH(pass VARCHAR(100), salt VARCHAR(100))
# RETURNS TEXT DETERMINISTIC
# RETURN SHA2(CONCAT(salt, pass, salt), 256) ;
