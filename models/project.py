import os, sys, shutil
import importlib
import fnmatch, glob
import traceback

from .base import DB


SRC_MAIN_PYTHON_STARTER = '''

def main():
    print("Hello World!")

'''

SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".txt": "plaintext",
}

FS_IGNORES = ["*.pyc", '__pycache__']



def handler(_exception_type, _value, t):
    # extract the stack summary
    summary = traceback.extract_tb(t)

    # replace file names for each frame summary
    for frame_summary in summary:
        filename = frame_summary.filename
        frame_summary.filename = os.path.relpath(filename)

    # rebuild the traceback
    print(''.join(traceback.format_list(traceback.StackSummary.from_list(summary))), file=sys.stderr)






class Project(DB):

    def __init__(self, workspace_path, db_path, user, project_id, name, name_hash, descr):
        super().__init__(db_path)
        self.workspace_path = workspace_path
        # if user.first_name!='sgop':
        #     raise Exception("Found it")

        self.project_id = project_id
        self.name = name
        self.name_hash = name_hash
        self.descr = descr
        self.user = user
        self.src_path = os.path.join(self.workspace_path, self.user.email, self.name)
        self._prep_src()


    def _prep_src(self):
        if not os.path.isdir(self.src_path):
            os.makedirs(self.src_path)

        main_path = os.path.join(self.src_path, 'main.py')
        if not os.path.isfile(main_path):
            with open(main_path, 'w') as m:
                m.write(SRC_MAIN_PYTHON_STARTER)


    def _get_file_dict(self, name, path):
        '''
        returns a dictionary describing a file with keys:
            name:str, type:str, path:str, language:str, selected:bool, src:str
        '''
        ext = os.path.splitext(path)[-1]
        out = {
            'name': name,
            'type': 'file',
            'path': os.path.relpath(path, self.src_path),
            'language': SUPPORTED_LANGUAGES.get(ext, ''),
            'selected': (name == "main.py"),
        }
        with open(path, 'r') as file:
            out['src'] = file.read()
        return out


    def _get_folder_dict(self, name, path):
        '''
        returns a dictionary describing a folder with keys:
            name:str, type:str, path:str, open:bool, children:list

        elements of 'children' can be files of folders
        '''
        return {
            'name': name,
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
                d.append(self._get_file_dict(name, f))

            elif os.path.isdir(f):
                d.append(self._get_folder_dict(name, f))
        return d


    def struct_to_dict(self):
        '''
        returns a list of dictionaries describing the full project with keys:
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


    def _run(self):
        curr_dir = os.getcwd()
        os.chdir(self.src_path)
        # caution: path[0] is reserved for script path (or '' in REPL)
        sys.path.insert(1, self.src_path)

        # import and immediately reload module to account for any changes
        # importlib.invalidate_caches()
        module = importlib.import_module('main')
        # importlib.reload(module)

        try:
            print("> imported", module.__name__, "from", os.path.join(self.user.email, self.name))

            res = module.main()
            print("> done")

        finally:
            sys.path.remove(self.src_path)
            os.chdir(curr_dir)

            print("> clean up sys.modules")
            to_remove = []
            for mod_name, mod in sys.modules.items():
                if hasattr(mod, '__file__') and mod.__file__ is not None and self.src_path in mod.__file__:
                    to_remove.append(mod_name)

            for mod_name in to_remove:
                del sys.modules[mod_name]

        return res


    def run(self):
        try:
            self._run()
        except:
            err = traceback.format_exc()
            err = err.replace(os.path.join(self.workspace_path, self.user.email), '')
            err = err.replace(self.workspace_path, '')
            # err = err.replace(CWD, '')
            print(err)


    def new_file(self, path, name):
        src = os.path.join(self.src_path, path)
        if not os.path.isdir(src):
            raise Exception(f"Path not found - {path}")
        fpath = os.path.join(src, name)

        if os.path.isfile(fpath):
            raise Exception(f"File exists - {os.path.join(path, name)}")

        with open(fpath, 'w') as f:
            f.write('\n')
        return self._get_file_dict(name, fpath)


    def save_file(self, path, src):
        pp = os.path.join(self.src_path, path)
        with open(pp, 'w') as f:
            f.write(src)
        return True


    def delete_file(self, path):
        pp = os.path.join(self.src_path, path)
        if os.path.isfile(pp):
            os.remove(pp)
            return True #self.struct_to_dict()
        raise Exception(f"Path not found - {path}")


    def new_folder(self, path, name):
        src = os.path.join(self.src_path, path)
        if not os.path.isdir(src):
            raise Exception(f"Path not found - {path}")
        fpath = os.path.join(src, name)

        if os.path.isdir(fpath):
            raise Exception(f"Folder exists - {os.path.join(path, name)}")

        os.makedirs(fpath)
        return self._get_folder_dict(name, fpath)


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
