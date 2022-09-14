import os, sys
import configparser
import importlib
import fnmatch, glob
import traceback


CWD = os.path.dirname(os.path.abspath(__file__))

default_config = {'projects_stash': 'projects'}
config = configparser.ConfigParser(defaults=default_config)
config.read(os.path.join(CWD, 'config.ini'))


PROJECTS_STASH = os.path.realpath(config['DEFAULT']['projects_stash'])
SRC_MAIN_PYTHON_STARTER = '''

def main():
    pass

'''

SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
}


class Project:

    def __init__(self, project_name, user_name):
        if user_name!='sgop':
            raise Exception("Found it")

        self.name = project_name
        self.user = user_name
        self.project_path = os.path.join(PROJECTS_STASH, self.user, self.name)
        self.src_path = os.path.join(self.project_path, 'src')
        if not os.path.isdir(self.src_path):
            os.makedirs(self.src_path)

        self.config_path = os.path.join(self.project_path, 'config.ini')
        self.config = configparser.ConfigParser()
        self._prep_config()
        self._prep_src()


    def _prep_config(self):
        self.config.read(self.config_path)
        if 'schedule' not in self.config:
            self.config.add_section('schedule')
            self.config['schedule']['every'] = ''
            self.config['schedule']['at'] = ''
            with open(self.config_path, 'w') as c:
                self.config.write(c)


    def _prep_src(self):
        main_path = os.path.join(self.src_path, 'main.py')
        if not os.path.isfile(main_path):
            with open(main_path, 'w') as m:
                m.write(SRC_MAIN_PYTHON_STARTER)


    def _get_file_dict(self, name, path):
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
        return {
            'name': name,
            'type': 'folder',
            'path': os.path.relpath(path, self.src_path),
            'open': True, # open by default??
            'children': self._children_to_list(path)
        }


    def _children_to_list(self, path):
        ignores = ["*.pyc", '__pycache__']
        d = []
        for f in glob.glob(os.path.join(path, "*")):
            name = os.path.basename(f)
            ignore = False
            for pat in ignores:
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
        return [{
            'name': f'{self.user}/{self.name}',
            'path':'',
            'type': 'folder',
            'children': self._children_to_list(self.src_path),
            'open': True
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
        print("> imported", module.__name__, "from", os.path.join(self.user, self.name))

        res = module.main()
        print("> done")

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
            err = err.replace(os.path.join(PROJECTS_STASH, self.user), '')
            err = err.replace(PROJECTS_STASH, '')
            err = err.replace(CWD, '')
            print(err)



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


if __name__ == '__main__':
    j = Project("test", "sgop")
    j.run()
    for d in j.struct_to_dict():
        print(d)
