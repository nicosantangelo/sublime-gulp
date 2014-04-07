import sublime
import os
from threading import Thread
import signal, subprocess
import json
from hashlib import sha1 

def is_sublime_text_3():
    return int(sublime.version()) >= 3000

if is_sublime_text_3():
    from .base_command import BaseCommand
else:
    from base_command import BaseCommand
    
class GulpCommand(BaseCommand):
    package_name = "Gulp"
    cache_file_name = ".sublime-gulp.cache"
    
    def work(self):
        self.set_instance_variables()
        self.list_gulp_files()

    def set_instance_variables(self):
        self.gulp_files = []
        self.env = Env(self.settings)

    def list_gulp_files(self):
        self.folders = []
        for folder_path in self.window.folders():
            self.folders.append(folder_path)
            self.append_to_gulp_files(folder_path)
        if len(self.gulp_files) > 0:
            self.choose_file()
        else:
            sublime.error_message("gulpfile.js or gulpfile.coffee not found!")

    def append_to_gulp_files(self, path):
        if os.path.exists(os.path.join(path, "gulpfile.js")):
            self.gulp_files.append(os.path.join(path, "gulpfile.js"))
        elif os.path.exists(os.path.join(path, "gulpfile.coffee")):
            self.gulp_files.append(os.path.join(path, "gulpfile.coffee"))

    def choose_file(self):
        if len(self.gulp_files) == 1:
            self.show_tasks_from_gulp_file(0)
        else:
            self.window.show_quick_panel(self.gulp_files, self.show_tasks_from_gulp_file)

    def show_tasks_from_gulp_file(self, file_index):
        if file_index > -1:
            self.working_dir = os.path.dirname(self.gulp_files[file_index])
            self.tasks = self.list_tasks()
            if self.tasks is not None:
                self.show_quick_panel(self.tasks, self.run_gulp_task)

    def list_tasks(self):
        try:
            self.callcount = 0
            json_result = self.fetch_json()
        except TypeError as e:
            sublime.error_message("SublimeGulp: JSON  cache (.sublime-gulp.cache) is malformed.\nCould not read available tasks\n")
        else:
            tasks = [[name, self.dependencies_text(task)] for name, task in json_result.items()]
            return sorted(tasks, key = lambda task: task)

    def dependencies_text(self, task):
        return "Dependencies: " + task['dependencies'] if task['dependencies'] else ""

    # Refactor
    def fetch_json(self):
        jsonfilename = os.path.join(self.working_dir, self.cache_file_name)
        gulpfile = os.path.join(self.working_dir, "gulpfile.js") # .coffee ?
        data = None

        if os.path.exists(jsonfilename):
            filesha1 = Security.hashfile(gulpfile)
            json_data = open(jsonfilename)

            try:
                data = json.load(json_data)
                if gulpfile in data and data[gulpfile]["sha1"] == filesha1:
                    return data[gulpfile]["tasks"]
            finally:
                json_data.close()

        self.callcount += 1

        if self.callcount == 1: 
            return self.write_to_cache()

        if data is None:
            raise TypeError("Could not write to cache gulpfile")

        raise TypeError("Sha1 from gulp cache ({0}) is not equal to calculated ({1})".format(data[gulpfile]["sha1"], filesha1))

    def write_to_cache(self):
        package_path = os.path.join(sublime.packages_path(), self.package_name)

        args = r'node "%s/write_tasks_to_cache.js"' % package_path # Test in ST2

        write_to_cache = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env.get_path_with_exec_args(), cwd=self.working_dir, shell=True)
        (stdout, stderr) = write_to_cache.communicate()

        if 127 == write_to_cache.returncode:
            sublime.error_message("\"node\" command not found.\nPlease be sure to have node installed and in your PATH.")
            return

        return self.fetch_json()

    def run_gulp_task(self, task_index):
        if task_index > -1:
            command = self.construct_command(task_index)
            # Option to kill on timeout. Check thread.isAlive or fire on sublime.set_async_timeout(kill, timeout)
            Thread(target = self.__run_command__, args = (command, )).start()

    def __run_command__(self, command):
            process = CrossPlatformProcess(self)
            process.run(command)
            if is_sublime_text_3():
                process.pipe_stdout(self.append_to_output_view)
            else:
                stdout, stin = process.communicate()
                sublime.set_timeout(lambda: self.append_to_output_view(stdout), 0)

    def construct_command(self, task_index):
        task_name = self.tasks[task_index][0]
        self.show_output_panel("Running %s...\n" % task_name)
        return r"gulp %s" % task_name


class GulpKillCommand(BaseCommand):
    def work(self):
        if not ProcessCache.empty():
            ProcessCache.kill_all()
            self.show_output_panel("All running tasks killed!\n")


class CrossPlatformProcess():
    def __init__(self, command):
        self.path = command.env.get_path_with_exec_args()
        self.working_dir = command.working_dir

    def run(self, cmd):
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.path, cwd=self.working_dir, shell=True, preexec_fn=self._preexec_val())
        ProcessCache.add(self)
        return self

    def _preexec_val(self):
        return os.setsid if sublime.platform() != "windows" else None

    def pipe_stdout(self, fn):
        for line in self.process.stdout:
            fn(str(line.rstrip().decode('utf-8')) + "\n")
        self.terminate()

    def communicate(self):
        return self.process.communicate()

    def terminate(self):
        self.process.terminate()
        ProcessCache.remove(self)

    def kill(self):
        pid = self.process.pid
        if sublime.platform() == "windows":
            kill_process = subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            kill_process.communicate()
        else:
            os.killpg(pid, signal.SIGTERM)


class ProcessCache():
    _procs = []

    @classmethod
    def add(cls, process):
       cls._procs.append(process)

    @classmethod
    def remove(cls, process):
        if process in cls._procs:
            cls._procs.remove(process)

    @classmethod
    def kill_all(cls):
        for process in cls._procs:
            process.kill()
        cls.clear()

    @classmethod
    def empty(cls):
        return len(cls._procs) == 0

    @classmethod
    def clear(cls):
        del cls._procs[:]


class Env():
    def __init__(self, settings):
        self.exec_args = settings.get('exec_args', False)

    def get_path(self):
        path = os.environ['PATH']
        if self.exec_args:
            path = exec_args.get('path', os.environ['PATH'])
        return str(path)

    def get_path_with_exec_args(self):
        env = os.environ.copy()
        if self.exec_args:
            path = str(exec_args.get('path', ''))
            if path:
                env['PATH'] = path
        return env


class Security():
    @classmethod
    def hashfile(cls, filename):
        with open(filename, mode='rb') as f:
            filehash = sha1()
            content = f.read();
            filehash.update(str("blob " + str(len(content)) + "\0").encode('UTF-8'))
            filehash.update(content)
            return filehash.hexdigest()