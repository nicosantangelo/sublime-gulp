import sys
import sublime
import sublime_plugin
import datetime
import codecs
import os, os.path
from threading import Thread
import signal, subprocess
import json
import webbrowser
from hashlib import sha1 

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .base_command import BaseCommand
    from .progress_notifier import ProgressNotifier
    import urllib.request as urllib2
else:
    from base_command import BaseCommand
    from progress_notifier import ProgressNotifier
    import urllib2

class GulpCommand(BaseCommand):
    cache_file_name = ".sublime-gulp.cache"
    log_file_name = 'sublime-gulp.log'
    
    def work(self):
        self.set_instance_variables()
        self.list_gulp_files()

    def set_instance_variables(self):
        self.gulp_files = []
        self.env = Env(self.settings)

    def list_gulp_files(self):
        self.append_paths()
        if len(self.gulp_files) > 0:
            self.choose_file()
        else:
            self.error_message("gulpfile.js not found!")

    def append_paths(self):
        self.folders = []
        for folder_path in self.window.folders():
            self.append_to_gulp_files(folder_path)
            for inner_folder in self.settings.get("gulpfile_paths", []):
                self.append_to_gulp_files(os.path.join(folder_path, inner_folder))


    def append_to_gulp_files(self, folder_path):
        gulpfile_path = os.path.join(folder_path, "gulpfile.js")
        self.folders.append(folder_path)
        if os.path.exists(gulpfile_path):
            self.gulp_files.append(gulpfile_path)

    def choose_file(self):
        if len(self.gulp_files) == 1:
            self.show_tasks_from_gulp_file(0)
        else:
            self.show_quick_panel(self.gulp_files, self.show_tasks_from_gulp_file)

    def show_tasks_from_gulp_file(self, file_index):
        if file_index > -1:
            self.working_dir = os.path.dirname(self.gulp_files[file_index])
            if self.task_name:
                self.run_gulp_task()
            else:
                self.defer(self.show_tasks)

    def show_tasks(self):
        self.tasks = self.list_tasks()
        if self.tasks is not None:
            self.show_quick_panel(self.tasks, self.task_list_callback)

    def list_tasks(self):
        try:
            self.callcount = 0
            json_result = self.fetch_json()
        except TypeError as e:
            self.error_message("Could not read available tasks.\nMaybe the JSON cache (.sublime-gulp.cache) is malformed?")
        except Exception as e:
            self.error_message(str(e))
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
            raise Exception("Could not write to cache gulpfile.")

        raise Exception("Sha1 from gulp cache ({0}) is not equal to calculated ({1}).\nTry erasing the cache and running Gulp again.".format(data[gulpfile]["sha1"], filesha1))

    def write_to_cache(self):
        package_path = os.path.join(sublime.packages_path(), self.package_name)

        args = r'node "%s/write_tasks_to_cache.js"' % package_path

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env.get_path_with_exec_args(), cwd=self.working_dir, shell=True)
        (stdout, stderr) = process.communicate()

        if 127 == process.returncode:
            raise Exception("\"node\" command not found.\nPlease be sure to have nodejs installed on your system and in your PATH (more info in the README).")
        elif stderr:
            self.log_errors(stderr)
            raise Exception("There was an error running gulp, make sure gulp is running correctly in your project.\nFor more info check the sublime-gulp.log file")

        return self.fetch_json()

    def log_errors(self, text):
        if not self.settings.get("log_errors", True):
            return
        log_path = self.working_dir + "/" + self.log_file_name
        header = "Remember that you can report errors and get help in https://github.com/NicoSantangelo/sublime-gulp" if not os.path.isfile(log_path) else ""
        with codecs.open(log_path, 'a', "utf-8") as log_file:
            log_file.write(header + "\n\n" + str(datetime.datetime.now().strftime("%m-%d-%Y %H:%M")) + ":\n" + text.decode('utf-8'))

    def task_list_callback(self, task_index):
        if task_index > -1:
            self.task_name = self.tasks[task_index][0]
            self.task_flag = self.get_flag_from_task_name()
            self.run_gulp_task()

    def run_gulp_task(self):
        task = self.construct_gulp_task()
        Thread(target = self.run_process, args = (task, )).start() # Option to kill on timeout?

    def construct_gulp_task(self):
        self.show_running_status_in_output_panel()
        return r"gulp %s %s" % (self.task_name, self.task_flag)

    def run_process(self, task):
        process = CrossPlatformProcess(self, self.nonblocking)
        process.run(task)
        stdout, stderr = process.communicate(self.append_to_output_view_in_main_thread)
        self.defer_sync(lambda: self.finish(stdout, stderr))

    def finish(self, stdout, stderr):
        finish_message = "gulp %s %s finished %s" % (self.task_name, self.task_flag, "with some errors." if stderr else "!")
        self.status_message(finish_message)
        if not self.silent:
            self.set_output_close_on_timeout()
        elif stderr and self.settings.get("show_silent_errors", False):
            self.silent = False
            self.show_running_status_in_output_panel()
            self.append_to_output_view(stdout)
            self.append_to_output_view(stderr)
            self.silent = True

    def show_running_status_in_output_panel(self):
        with_flag_text = (' with %s' % self.task_flag) if self.task_flag else ''
        self.show_output_panel("Running '%s'%s...\n" % (self.task_name, with_flag_text))


class GulpKillCommand(BaseCommand):
    def work(self):
        if ProcessCache.empty():
            self.status_message("There are no running tasks")
        else:
            self.show_output_panel("\nFinishing the following running tasks:\n")
            ProcessCache.each(lambda process: self.append_to_output_view("$ %s\n" % process.last_command.rstrip()))
            ProcessCache.kill_all()
            self.append_to_output_view("\nAll running tasks killed!\n")


class GulpShowPanelCommand(BaseCommand):
    def work(self):
        self.show_panel()


class GulpPluginsCommand(BaseCommand):
    def work(self):
        self.plugins = None
        self.request_plugin_list()

    def request_plugin_list(self):
        progress = ProgressNotifier("Gulp: Working")
        thread = PluginRegistryCall()
        thread.start()
        self.handle_thread(thread, progress)

    def handle_thread(self, thread, progress):
        if thread.is_alive() and not thread.error:
            sublime.set_timeout(lambda: self.handle_thread(thread, progress), 100)
        else:
            progress.stop()
            if thread.result:
                plugin_response = json.loads(thread.result.decode('utf-8'))
                self.plugins = PluginList(plugin_response)
                self.show_quick_panel(self.plugins.quick_panel_list(), self.open_in_browser, font = 0)
            else:
                self.error_message(self.error_text_for(thread))

    def error_text_for(self, thread):
        tuple = (
            "The plugin repository seems to be down.",
            "If the site at http://gulpjs.com/plugins is working, please report this issue at the Sublime Gulp repo.",
            "Thanks!",
            thread.error
        )
        return "\n\n%s\n\n%s\n\n%s\n\n%s" % tuple

    def open_in_browser(self, index = -1):
        if index >= 0 and index < self.plugins.length:
            webbrowser.open_new(self.plugins.get(index).get('homepage'))

class GulpDeleteCacheCommand(GulpCommand):
    def choose_file(self):
        if len(self.gulp_files) == 1:
            self.delete_cache(0)
        else:
            self.show_quick_panel(self.gulp_files, self.delete_cache)

    def delete_cache(self, file_index):
        if file_index > -1:
            self.working_dir = os.path.dirname(self.gulp_files[file_index])
            try:
                jsonfilename = os.path.join(self.working_dir, GulpCommand.cache_file_name)
                if os.path.exists(jsonfilename):
                    os.remove(jsonfilename)
                    self.status_message('Cache removed successfully')
            except Exception as e:
                self.status_message("Could not remove cache: %s" % str(e))


class GulpExitCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            self.window.run_command("gulp_kill")
        finally:
            self.window.run_command("exit")

class CrossPlatformProcess():
    def __init__(self, command, nonblocking=True):
        self.path = command.env.get_path_with_exec_args()
        self.working_dir = command.working_dir
        self.last_command = ""
        self.nonblocking = nonblocking

    def run(self, command):
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.path, cwd=self.working_dir, shell=True, preexec_fn=self._preexec_val())
        self.last_command = command
        ProcessCache.add(self)
        return self

    def _preexec_val(self):
        return os.setsid if sublime.platform() != "windows" else None

    def communicate(self, fn = lambda x:None):
        stdout, stderr = self.pipe(fn)
        self.process.communicate()
        self.terminate()
        return (stdout, stderr)

    def pipe(self, fn):
        streams = [self.process.stdout, self.process.stderr]
        streams_text = []
        if self.nonblocking:
            threads = [ThreadWithResult(target=self._pipe_stream, args=(stream, fn)) for stream in streams]
            [t.join() for t in threads]
            streams_text = [t.result for t in threads]
        else:
            streams_text = [self._pipe_stream(stream, fn) for stream in streams]
        return streams_text

    def _pipe_stream(self, stream, fn):
        output_text = ""
        while True:
            line = stream.readline()
            if not line: break
            output_line = self.decode_line(line)
            output_text += output_line
            fn(output_line)
        return output_text

    def decode_line(self, line):
        line = line.rstrip()
        return str(line.decode('utf-8') if sys.version_info >= (3, 0) else line) + "\n"

    def read(self, stream):
        return stream.read().decode('utf-8')

    def terminate(self):
        if self.is_alive():
            self.process.terminate()
        ProcessCache.remove(self)

    def is_alive(self):
        return self.process.poll() is None

    def kill(self):
        pid = self.process.pid
        if sublime.platform() == "windows":
            kill_process = subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            kill_process.communicate()
        else:
            os.killpg(pid, signal.SIGTERM)
        ProcessCache.remove(self)


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
        cls.each(lambda process: process.kill())
        cls.clear()

    @classmethod
    def each(cls, fn):
        for process in cls._procs:
            fn(process)

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
            path = self.exec_args.get('path', os.environ['PATH'])
        return str(path)

    def get_path_with_exec_args(self):
        env = os.environ.copy()
        if self.exec_args:
            path = str(self.exec_args.get('path', ''))
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


class PluginList():
    def __init__(self, plugins_response):
        self.plugins = [Plugin(plugin_json) for plugin_json in plugins_response["results"]]
        self.length = len(self.plugins)

    def get(self, index):
        if index >= 0 and index < self.length:
            return self.plugins[index]

    def quick_panel_list(self):
        return [ [plugin.name + ' (' + plugin.version + ')', plugin.description] for plugin in self.plugins ]

class Plugin():
    def __init__(self, plugin_json):
        self.plugin = plugin_json
        self.set_attributes()

    def set_attributes(self):
        self.name = self.get('name')
        self.version = "v" + self.get('version')
        self.description = self.get('description')

    def get(self, property):
        return self.plugin[property] if self.has(property) else ''

    def has(self, property):
        return property in self.plugin


class PluginRegistryCall(Thread):
    url = "http://npmsearch.com/query?fields=name,description,homepage,version,rating&q=keywords:gulpfriendly&q=keywords:gulpplugin&size=1755&sort=rating:desc&start=20"

    def __init__(self, timeout = 5):
        self.timeout = timeout
        self.result = None
        self.error = None
        Thread.__init__(self)

    def run(self):
        try:
            request = urllib2.Request(self.url, None, headers = { "User-Agent": "Sublime Text" })
            http_file = urllib2.urlopen(request, timeout = self.timeout)
            self.result = http_file.read()
            return

        except urllib2.HTTPError as e:
            err = 'Error: HTTP error %s contacting gulpjs registry' % (str(e.code))
        except urllib2.URLError as e:
            err = 'Error: URL error %s contacting gulpjs registry' % (str(e.reason))

        self.error = err
        self.result = None

class ThreadWithResult(Thread):
    def __init__(self, target, args):
        self.result = None
        self.target = target
        self.args = args
        Thread.__init__(self)
        self.start()

    def run(self):
        self.result = self.target(*self.args)
