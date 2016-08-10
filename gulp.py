import sublime
import sublime_plugin
import traceback
import codecs
import os
from datetime import datetime
from threading import Thread
import signal
import subprocess
import json
import webbrowser

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .base_command import BaseCommand
    from .progress_notifier import ProgressNotifier
    from .cross_platform_codecs import CrossPlaformCodecs
    from .hasher import Hasher
    from .gulp_version import GulpVersion
    from .dir_context import Dir
    from .plugins import PluginList, PluginRegistryCall
else:
    from base_command import BaseCommand
    from progress_notifier import ProgressNotifier
    from cross_platform_codecs import CrossPlaformCodecs
    from hasher import Hasher
    from gulp_version import GulpVersion
    from dir_context import Dir
    from plugins import PluginList, PluginRegistryCall


#
# Commands
#


class GulpCommand(BaseCommand):
    cache_file_name = ".sublime-gulp.cache"
    log_file_name = 'sublime-gulp.log'
    allowed_extensions = [".babel.js", ".js"]

    def work(self):
        self.folders = []
        self.gulp_files = []
        self.list_gulp_files()

    def list_gulp_files(self):
        self.append_paths()

        if not self.check_for_gulpfile:
            self.gulp_files = self.folders

        if len(self.gulp_files) > 0:
            self.choose_file()
        else:
            sufix = "on:\n- %s" % "\n- ".join(self.sercheable_folders) if len(self.sercheable_folders) > 0 else ""
            self.error_message("gulpfile not found %s" % sufix)

    def append_paths(self):
        for folder_path in self.sercheable_folders:
            self.append_to_gulp_files(folder_path)
            for inner_folder in self.settings.get("gulpfile_paths", []):
                if(os.name == 'nt'):
                    inner_folder = inner_folder.replace("/", "\\")
                self.append_to_gulp_files(os.path.join(folder_path, inner_folder))

    def append_to_gulp_files(self, folder_path):
        gulpfile_path = self.get_gulpfile_path(folder_path)
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
            self.working_dir = self.gulp_files[file_index]
            if self.task_name is not None:
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
            print(traceback.format_exc())
            self.error_message(str(e))
        else:
            tasks = [[name, self.dependencies_text(task)] for name, task in json_result.items()]
            return sorted(tasks, key=lambda task: task)

    def dependencies_text(self, task):
        return "Dependencies: " + task['dependencies'] if task['dependencies'] else ""

    def fetch_json(self):
        jsonfilename = os.path.join(self.working_dir, GulpCommand.cache_file_name)
        gulpfile = self.get_gulpfile_path(self.working_dir)
        data = None

        if os.path.exists(jsonfilename):
            filesha1 = Hasher.sha1(gulpfile)
            json_data = codecs.open(jsonfilename, "r", "utf-8", errors='replace')

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

        if gulpfile in data:
            raise Exception("Sha1 from gulp cache ({0}) is not equal to calculated ({1}).\nTry erasing the cache and running Gulp again.".format(data[gulpfile]["sha1"], filesha1))
        else:
            raise Exception("Have you renamed a folder?.\nSometimes Sublime doesn't update the project path, try removing the folder from the project and adding it again.")

    def write_to_cache(self):
        package_path = os.path.join(sublime.packages_path(), self.package_name)

        process = CrossPlatformProcess(self)
        (stdout, stderr) = process.run_sync(r'node "%s/write_tasks_to_cache.js"' % package_path)

        if process.failed:
            try:
                self.write_to_cache_without_js()
            except:
                if process.returncode() == 127:
                    raise Exception("\"node\" command not found.\nPlease be sure to have nodejs installed on your system and in your PATH (more info in the README).")
                elif stderr:
                    self.log_errors(stderr)
                    raise Exception("There was an error running gulp, make sure gulp is running correctly in your project.\nFor more info check the sublime-gulp.log file")

        return self.fetch_json()

    def write_to_cache_without_js(self):
        process = CrossPlatformProcess(self)
        (stdout, stderr) = process.run_sync(r'gulp -v')

        if process.failed or not GulpVersion(stdout).supports_tasks_simple():
            raise Exception("Gulp: Could not get the current gulp version or your gulp CLI version is lower than 3.7.0")

        (stdout, stderr) = process.run_sync(r'gulp --tasks-simple')

        gulpfile = self.get_gulpfile_path(self.working_dir)

        if not stdout:
            raise Exception("Gulp: The result of `gulp --tasks-simple` was empty")

        self.write_cache_file({
            gulpfile: {
                "sha1": Hasher.sha1(gulpfile),
                "tasks": dict((task, { "name": task, "dependencies": "" }) for task in stdout.split("\n") if task)
            }
        })

    def write_cache_file(self, cache):
        cache_path = os.path.join(self.working_dir, GulpCommand.cache_file_name)
        with codecs.open(cache_path, "w", "utf-8", errors='replace') as cache_file:
            json_cache = json.dumps(cache, ensure_ascii=False)
            cache_file.write(json_cache)

    def get_gulpfile_path(self, base_path):
        for extension in GulpCommand.allowed_extensions:
            gulpfile_path = os.path.join(base_path, "gulpfile" + extension)
            if os.path.exists(gulpfile_path):
                return gulpfile_path
        return gulpfile_path

    def log_errors(self, text):
        if not self.settings.get("log_errors", True):
            return
        log_path = os.path.join(self.working_dir, GulpCommand.log_file_name)
        header = "Remember that you can report errors and get help in https://github.com/NicoSantangelo/sublime-gulp" if not os.path.isfile(log_path) else ""
        timestamp = str(datetime.now().strftime("%m-%d-%Y %H:%M"))

        with codecs.open(log_path, "a", "utf-8", errors='replace') as log_file:
            log_file.write(header + "\n\n" + timestamp + ":\n" + text)

    def task_list_callback(self, task_index):
        if task_index > -1:
            self.task_name = self.tasks[task_index][0]
            self.task_flag = self.get_flag_from_task_name()
            self.run_gulp_task()

    def run_gulp_task(self):
        task = self.construct_gulp_task()
        Thread(target=self.run_process, args=(task, )).start()

    def construct_gulp_task(self):
        self.show_running_status_in_output_panel()
        return r"gulp %s %s" % (self.task_name, self.task_flag)

    def run_process(self, task):
        process = CrossPlatformProcess(self)
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


class GulpArbitraryCommand(GulpCommand):
    def show_tasks_from_gulp_file(self, file_index):
        if file_index > -1:
            self.working_dir = self.gulp_files[file_index]
            self.show_input_panel(caption="gulp", on_done=self.after_task_input)

    def after_task_input(self, task_name=None):
        if task_name:
            self.task_name = task_name
            self.task_flag = ''
            self.run_gulp_task()


class GulpLastCommand(BaseCommand):
    def work(self):
        if ProcessCache.last:
            last_command = ProcessCache.last.last_command
            task_name = last_command.replace('gulp ', '').strip()
            self.window.run_command("gulp", { "task_name": task_name })
        else:
            self.status_message("You need to run a task first")


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


class GulpHidePanelCommand(BaseCommand):
    def work(self):
        self.close_panel()


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
                self.show_quick_panel(self.plugins.quick_panel_list(), self.open_in_browser, font=0)
            else:
                self.error_message(self.error_text_for(thread))

    def error_text_for(self, thread):
        error_tuple = (
            "The plugin repository seems to be down.",
            "If http://gulpjs.com/plugins is working, please report this issue at the Sublime Gulp repo (https://github.com/NicoSantangelo/sublime-gulp).",
            "Thanks!",
            thread.error
        )
        return "\n\n%s\n\n%s\n\n%s\n\n%s" % error_tuple

    def open_in_browser(self, index=-1):
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
            self.working_dir = self.gulp_files[file_index]
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


#
# General purpose Classes.
#


class CrossPlatformProcess():
    def __init__(self, sublime_command):
        self.working_dir = sublime_command.working_dir
        self.nonblocking = sublime_command.nonblocking
        self.path = Env.get_path(sublime_command.exec_args)
        self.last_command = ""
        self.failed = False

    def run(self, command):
        with Dir.cd(self.working_dir):
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.path, shell=True, preexec_fn=self._preexec_val())

        self.last_command = command
        ProcessCache.add(self)
        return self

    def run_sync(self, command):
        command = CrossPlaformCodecs.encode_process_command(command)

        with Dir.cd(self.working_dir):
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.path, shell=True)
            (stdout, stderr) = self.process.communicate()
            self.failed = self.process.returncode == 127 or stderr

        return (CrossPlaformCodecs.force_decode(stdout), CrossPlaformCodecs.force_decode(stderr))

    def _preexec_val(self):
        return os.setsid if sublime.platform() != "windows" else None

    def communicate(self, fn=lambda x: None):
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
            if not line:
                break
            output_line = CrossPlaformCodecs.decode_line(line)
            output_text += output_line
            fn(output_line)
        return output_text

    def terminate(self):
        if self.is_alive():
            self.process.terminate()
        ProcessCache.remove(self)

    def is_alive(self):
        return self.process.poll() is None

    def returncode(self):
        return self.process.returncode

    def kill(self):
        pid = self.process.pid
        if sublime.platform() == "windows":
            kill_process = subprocess.Popen(['C:\\Windows\\system32\\taskkill.exe', '/F', '/T', '/PID', str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            kill_process.communicate()
        else:
            os.killpg(pid, signal.SIGTERM)
        ProcessCache.remove(self)


class ProcessCache():
    _procs = []
    last = None

    @classmethod
    def add(cls, process):
        cls._procs.append(process)
        cls.last = process

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
    @classmethod
    def get_path(self, exec_args=False):
        env = os.environ.copy()
        if exec_args:
            path = str(exec_args.get('path', ''))
            if path:
                env['PATH'] = path
        return env


class ThreadWithResult(Thread):
    def __init__(self, target, args):
        self.result = None
        self.target = target
        self.args = args
        Thread.__init__(self)
        self.start()

    def run(self):
        self.result = self.target(*self.args)
