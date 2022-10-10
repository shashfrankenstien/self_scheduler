import os, sys, shutil
import importlib
import fnmatch, glob
import traceback
from datetime import datetime as dt
import threading
import re
import sqlite3

from .base import DB
from .capture import print_capture


SRC_MAIN_PYTHON_STARTER = '''

def main():
    print("Hello World!")

'''

# SRC_CONFIG_STARTER = '''
# [main]
# file = main.py
# func = main

# [schedule]
# every =
# at =
# timezone =

# '''


SRC_README_STARTER = '''
Self Scheduler Project
=======================

This is a project created to be used with self-scheduler application.

'''



SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".json": "json",
    ".txt": "plaintext",
    ".md": "markdown",
    ".ini": "ini"
}

FS_IGNORES = ["*.pyc", '__pycache__']



# def handler(_exception_type, _value, t):
#     # extract the stack summary
#     summary = traceback.extract_tb(t)

#     # replace file names for each frame summary
#     for frame_summary in summary:
#         filename = frame_summary.filename
#         frame_summary.filename = os.path.relpath(filename)

#     # rebuild the traceback
#     print(''.join(traceback.format_list(traceback.StackSummary.from_list(summary))), file=sys.stderr)






class Project(DB):

    def __init__(self, workspace_path, db_path, user, project_id, name, name_hash, descr):
        super().__init__(db_path)
        self.workspace_path = workspace_path
        self.project_id = project_id
        self.name = name
        self.name_hash = name_hash
        self.descr = descr
        self.user = user
        self._src_path = None

        self._is_running = False


    @property
    def src_path(self):
        if self._src_path is None:
            # # flip email around to get the user's workspace folder
            # uname, domain = str(self.user.email).split("@", 1)
            # domain_elems = domain.split(".")
            # workspace_fldr = '.'.join(reversed(domain_elems)) + "." + uname
            workspace_fldr = self.user.email

            self._src_path = os.path.join(self.workspace_path, workspace_fldr, self.name)
            if not os.path.isdir(self._src_path):
                os.makedirs(self._src_path)

        return self._src_path


    def create_default_files(self):
        '''create default files. should be called the first time a project is created'''
        main_path = os.path.join(self.src_path, 'main.py')
        if not os.path.isfile(main_path):
            with open(main_path, 'w') as m:
                m.write(SRC_MAIN_PYTHON_STARTER)

        # config_path = os.path.join(self.src_path, 'main.ini')
        # if not os.path.isfile(config_path):
        #     with open(config_path, 'w') as m:
        #         m.write(SRC_CONFIG_STARTER.strip()+'\n')

        readme_path = os.path.join(self.src_path, 'README.txt')
        if not os.path.isfile(readme_path):
            with open(readme_path, 'w') as m:
                m.write(SRC_README_STARTER.strip()+'\n')


    def create_default_entry_point(self):
        '''create default entry point. should be called the first time a project is created'''
        ep = self.get_default_entry_point()
        if ep is not None:
            return ep

        self.create_entry_point("main.py", "main", is_default=True)
        return self.get_default_entry_point()


    def get_default_entry_point(self):
        return self.execute(
            f"SELECT file, func FROM entry_points WHERE project_id = {self.project_id} AND is_default = 1;",
            fetch_one=True
        )


    def create_entry_point(self, file, func, is_default: bool=False):
        src_dict = self.get_file_src(path=file)
        definition = f"^def\s*{func}\s*\(\):\s*$"

        matches = []
        for line in src_dict['src'].split('\n'):
            matches = re.findall(definition, line.strip())
            if matches:
                break

        if not matches:
            raise Exception(f"function '{func}' not found")

        conn = self.get_connection()
        try:
            if is_default:
                # mark all others as not default
                self.execute(f'''
                    UPDATE entry_points
                    SET is_default = 0
                    WHERE project_id = {self.project_id}
                ''', conn=conn)

            self.execute(f'''
                INSERT INTO entry_points (
                    project_id, file, func, is_default, create_dt
                )
                VALUES (
                    {self.project_id}, '{file}', '{func}', {1 if is_default else 0},
                    '{dt.now().strftime('%Y-%m-%d %H:%M:%S')}'
                );
            ''', conn=conn)
            conn.commit()
        except sqlite3.IntegrityError as e:
            if 'unique constraint failed' in str(e).lower():
                raise Exception("Entry point already exists") from e
            raise
        finally:
            conn.close()


    def delete_entry_point(self, epid):
        self.execute(f'''DELETE FROM entry_points WHERE project_id = {self.project_id} AND id = {epid};''')


    def get_entry_point(self, epid=None):
        if epid is None:
            return self.get_default_entry_point()
        ep = self.execute(
            f"SELECT file, func FROM entry_points WHERE project_id = {self.project_id} AND id = {epid};",
            fetch_one=True
        )
        if ep is None:
            raise Exception(f"Entry point {epid} not found.")
        return ep


    def get_all_entry_points(self):
        eps = self.execute(f'''
            SELECT
            p.name || ':' || ep.file || ':' || ep.func as name,
            ep.*
            FROM projects p
            LEFT JOIN entry_points ep
                ON p.id = ep.project_id
            WHERE p.id = {self.project_id}
            order by ep.id
        ''')
        if len(eps)==1 and eps[0].name is None:
            return []
        return [ep._asdict() for ep in eps]


    def get_full_schedule(self):
        scheds = self.execute(f'''
            SELECT
            p.name || ':' || ep.file || ':' || ep.func as name,
            sched.*
            FROM projects p
            LEFT JOIN entry_points ep
                ON p.id = ep.project_id
            LEFT JOIN schedule sched
                ON ep.id = sched.ep_id
            WHERE p.id = {self.project_id}
            AND sched.id IS NOT NULL
            order by sched.id
        ''')
        if len(scheds)==1 and scheds[0].name is None:
            return []
        return [s._asdict() for s in scheds]


    def get_properties(self):
        return {
            'entry_points':self.get_all_entry_points(),
            'schedule': self.get_full_schedule(),
        }


    def _get_file_dict(self, path):
        '''
        returns a dictionary describing a file with keys:
            name:str, type:str, path:str, selected:bool
        '''
        name = os.path.basename(path)
        ext = os.path.splitext(path)[-1]
        out = {
            'name': name,
            'type': 'file',
            'path': os.path.relpath(path, self.src_path),
            'language': SUPPORTED_LANGUAGES.get(ext, ''),
            'selected': (name == "main.py"),
        }
        return out


    def _get_folder_dict(self, path):
        '''
        returns a dictionary describing a folder with keys:
            name:str, type:str, path:str, open:bool, children:list

        elements of 'children' can be files of folders
        '''
        return {
            'name': os.path.basename(path),
            'type': 'folder',
            'path': os.path.relpath(path, self.src_path),
            'open': True, # open by default??
            'children': self._children_to_list(path)
        }


    def _children_to_list(self, path):
        d = []
        for f in glob.glob(os.path.join(path, "*")):
            name = os.path.basename(f)
            ignore = False
            for pat in FS_IGNORES:
                if fnmatch.fnmatch(name, pat):
                    ignore = True
                    break
            if ignore:
                continue

            if os.path.isfile(f):
                d.append(self._get_file_dict(f))

            elif os.path.isdir(f):
                d.append(self._get_folder_dict(f))
        return d


    def get_file_struct_dict(self):
        '''
        returns a list of dictionaries describing the full project files with keys:
            name:str, type:str, path:str, open:bool, children:list

        elements of 'children' can be files of folders
        '''
        return [{
            'name': self.name,
            'type': 'folder',
            'path':'',
            'open': True, # open by default
            'children': self._children_to_list(self.src_path),
        }]


    def get_file_src(self, path):
        '''
        returns a dictionary with file src:
            src:str, language:str
        '''
        full_path = os.path.join(self.src_path, path)
        if not os.path.isfile(full_path):
            raise ValueError(f"'{path}' not a file")

        ext = os.path.splitext(path)[-1]
        with open(full_path, 'r') as file:
            return {
                'language': SUPPORTED_LANGUAGES.get(ext, ''),
                'src': file.read()
            }


    def new_file(self, path, name):
        src = os.path.join(self.src_path, path)
        if not os.path.isdir(src):
            raise Exception(f"Path not found - {path}")
        fpath = os.path.join(src, name)

        if os.path.isfile(fpath):
            raise Exception(f"File exists - {os.path.join(path, name)}")

        with open(fpath, 'w') as f:
            f.write('\n')
        return self._get_file_dict(fpath)


    def save_file(self, path, src):
        pp = os.path.join(self.src_path, path)
        with open(pp, 'w') as f:
            f.write(src)
        return True


    def delete_file(self, path):
        pp = os.path.join(self.src_path, path)
        if os.path.isfile(pp):
            os.remove(pp)
            return True #self.get_file_struct_dict()
        raise Exception(f"Path not found - {path}")


    def new_folder(self, path, name):
        src = os.path.join(self.src_path, path)
        if not os.path.isdir(src):
            raise Exception(f"Path not found - {path}")
        fpath = os.path.join(src, name)

        if os.path.isdir(fpath):
            raise Exception(f"Folder exists - {os.path.join(path, name)}")

        os.makedirs(fpath)
        return self._get_folder_dict(fpath)


    def delete_folder(self, path, force: bool=False):
        fldr = os.path.join(self.src_path, path)
        if not os.path.isdir(fldr):
            raise Exception(f"Path not found - {path}")

        if force is True:
            shutil.rmtree(fldr)
            return True

        dir_empty = True
        for f in glob.glob(os.path.join(fldr, "*")):
            name = os.path.basename(f)
            ignore = False
            for pat in FS_IGNORES:
                if fnmatch.fnmatch(name, pat):
                    ignore = True
                    break
            if not ignore:
                dir_empty = False
                break

        if dir_empty:
            shutil.rmtree(fldr)
        else:
            raise Exception("Directory not empty")
        return True


    def rename(self, path, name):
        src = os.path.join(self.src_path, path)
        if not os.path.isdir(src) and not os.path.isfile(src):
            raise Exception(f"Path not found - {path}")

        dst = os.path.join(os.path.dirname(src), name)
        if (os.path.isdir(src) and os.path.isdir(dst)) or (os.path.isfile(src) and os.path.isfile(dst)):
            raise Exception(f"Name already exists")

        os.rename(src, dst)
        return True




    def _run(self, epid=None):
        self._is_running = True
        orig_dir = os.getcwd()
        orig_syspath = sys.path.copy()

        # caution: path[0] is reserved for script path (or '' in REPL)
        sys.path.remove(sys.path[0])
        sys.path.insert(0, self.src_path)
        os.chdir(self.src_path)

        # read config
        ep = self.get_entry_point(epid)
        print(ep)
        main_file = os.path.realpath(ep.file)
        main_function = ep.func

        if not os.path.isfile(main_file):
            raise FileNotFoundError(f"{main_file} file not found")

        main_path = os.path.dirname(main_file)
        main_file = os.path.splitext(os.path.basename(main_file))[0]
        if main_path not in sys.path: # if main_file is in a subfolder, it should be added to sys.path for import to work
            sys.path.insert(0, main_path)

        # import and immediately reload module to account for any changes
        module = importlib.import_module(main_file)

        try:
            print(f"> imported {module.__name__} from {os.path.join(self.user.email, self.name)}\n")
            runner = getattr(module, main_function)
            res = runner()
            print("\n> done")

        finally:
            sys.path = orig_syspath
            os.chdir(orig_dir)

            print("> clean up sys.modules")
            to_remove = []
            for mod_name, mod in sys.modules.items():
                if hasattr(mod, '__file__') and mod.__file__ is not None and self.src_path in mod.__file__:
                    to_remove.append(mod_name)

            for mod_name in to_remove:
                del sys.modules[mod_name]

            self._is_running = False
        return res


    def _run_print_wrapper(self, epid, msg_cb):
        with print_capture(msg_cb):
            try:
                self._run(epid)
            except:
                err = traceback.format_exc()
                err = err.replace(os.path.join(self.workspace_path, self.user.email), '')
                err = err.replace(self.workspace_path, '')
                # err = err.replace(CWD, '')
                print(err)

    # def run(self): # not used
    #     msgs = []
    #     def _cb(msg):
    #         msgs.append(str(msg))

    #     self._run_print_wrapper(msg_cb=_cb)
    #     return msgs


    def create_run_thread(self, epid, msg_queue):

        def _thread_target():
            def _cb(msg):
                msg_queue.put_nowait(str(msg))

            self._run_print_wrapper(epid, msg_cb=_cb)

        t = threading.Thread(target=_thread_target)
        t.daemon = True # makes sure it dies with parent process
        return t

