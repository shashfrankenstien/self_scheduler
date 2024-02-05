import re
import hashlib
from datetime import datetime as dt
from typing import List

from .base import DB
from .project import Project




class LoginError(Exception):
    pass



class User(DB):

    def __init__(self, workspace_path, db_path, email):
        super().__init__(db_path)
        if not User.email_format_ok(email):
            raise Exception("Invalid email")
        u = self.execute(f'''SELECT * FROM users WHERE email = '{email}' ''', fetch_one=True)
        if u is None:
            raise LoginError("Incorrect credentials")

        self.workspace_path = workspace_path
        self.email = email
        self.user_id = u.id
        self.first_name = u.first_name
        self.last_name = u.last_name
        self.salt = u.salt
        self.password = u.password # hashed
        self.logged_in = False

        hashed_email = hashlib.md5(self.email.strip().lower().encode()).hexdigest()
        self.gravatar_url = f'https://www.gravatar.com/avatar/{hashed_email}?s=200&d=retro'


    @staticmethod
    def email_format_ok(email):
        return re.match(r".*\@.*\..*", str(email)) != None


    def login(self, password):
        if password == "":
            raise ValueError("missing required fields")

        passhash = self.hash_password(password=password, salt=self.salt)
        if self.password != passhash:
            raise LoginError("Incorrect credentials")

        self.logged_in = True
        return self


    def check_logged_in(self):
        if not self.logged_in:
            raise LoginError("Incorrect credentials")


    def get_projects_dict(self):
        self.check_logged_in() # ensure user is logged in
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


    def get_all_projects(self) -> List[Project]:
        self.check_logged_in() # ensure user is logged in
        projects = []
        res = self.execute(f'''SELECT * FROM projects WHERE user_id = {self.user_id}''')
        for r in res:
            if r.id is None:
                continue
            p = Project(self.workspace_path, self.db_path, self, r.id, r.name, r.name_hash, r.descr)
            projects.append(p)
        return projects


    def project_exists(self, name_hash):
        res = self.execute(f'''
            SELECT id FROM projects WHERE user_id = {self.user_id} AND name_hash = '{name_hash}'
        ''', fetch_one=True)
        return res is not None


    def get_project(self, name_hash):
        self.check_logged_in() # ensure user is logged in
        res = self.execute(f'''SELECT id, name, descr FROM projects WHERE user_id = {self.user_id} AND name_hash = '{name_hash}' ''', fetch_one=True)
        if res is None:
            raise Exception("Project not found")
        return Project(self.workspace_path, self.db_path, self, res.id, res.name, name_hash, res.descr)


    def create_new_project(self, name, descr):
        self.check_logged_in() # ensure user is logged in
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

