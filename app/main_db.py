import os
from datetime import datetime as dt

from .base import DB
from .user import User, LoginError

from . import ss_sched


__SS_DB_SINGLETON = None

def get_ss_db_object(workspace_path):
    global __SS_DB_SINGLETON
    if __SS_DB_SINGLETON is None:
        __SS_DB_SINGLETON = SelfSchedulerDB(workspace_path)
    return __SS_DB_SINGLETON


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
            u.logged_in = True # Force logged in just for this function
            for p in u.get_all_projects():
                p.reload_schedules()


    def get_user(self, email):
        return User(self.workspace_path, self.db_path, email)


    def create_new_user(self, first_name, last_name, email, password):
        if first_name == "" or last_name == "" or email == "" or password == "":
            raise ValueError("missing required fields")

        if not User.email_format_ok(email):
            raise Exception("Invalid email")

        res = self.execute(f'''SELECT email FROM users WHERE email = '{email}' ''', fetch_one=True)
        if res is not None:
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





# SHOW FUNCTION STATUS
# WHERE db = "self_scheduler"

# SHOW TABLES FROM self_scheduler
# SHOW FULL TABLES IN self_scheduler

# create function if not exists self_scheduler.PASS_HASH(pass VARCHAR(100), salt VARCHAR(100))
# RETURNS TEXT DETERMINISTIC
# RETURN SHA2(CONCAT(salt, pass, salt), 256) ;
