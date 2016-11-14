import sublime
import sublime_plugin
import traceback
import codecs
import os
from datetime import datetime
from threading import Thread
import json
import webbrowser

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .base_command import BaseCommand
    from .settings import Settings
    from .progress_notifier import ProgressNotifier
    from .cross_platform_process import CrossPlatformProcess
    from .hasher import Hasher
    from .gulp_version import GulpVersion
    from .plugins import PluginList, PluginRegistryCall
    from .caches import ProcessCache, CacheFile
    from .timeout import set_timeout, defer, defer_sync, async
else:
    from base_command import BaseCommand
    from settings import Settings
    from progress_notifier import ProgressNotifier
    from cross_platform_process import CrossPlatformProcess
    from hasher import Hasher
    from gulp_version import GulpVersion
    from plugins import PluginList, PluginRegistryCall
    from caches import ProcessCache, CacheFile
    from timeout import set_timeout, defer, defer_sync, async


#
# Commands
#


class GulpCommand(BaseCommand):
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
            if not self.settings.get("recursive_gulpfile_search", False):
                sufix += '\n\nCheck the recursive_gulpfile_search setting for nested gulpfiles'
            self.error_message("gulpfile not found %s" % sufix)

    def append_paths(self):
        gulpfile_paths = self.settings.get("gulpfile_paths", [])
        ignored_gulpfile_folders = self.settings.get("ignored_gulpfile_folders", [])

        if self.settings.get("recursive_gulpfile_search", False):
            for folder_path in self.sercheable_folders:
                for dir, dirnames, files in os.walk(folder_path):
                    dirnames[:] = [dirname for dirname in dirnames if dirname not in ignored_gulpfile_folders]
                    self.append_to_gulp_files(dir)
        else:
            for folder_path in self.sercheable_folders:
                self.append_to_gulp_files(folder_path)
                for inner_folder in gulpfile_paths:
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
                defer(self.show_tasks)

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
        cache_file = CacheFile(self.working_dir)
        gulpfile = self.get_gulpfile_path(self.working_dir)
        data = None

        if cache_file.exists():
            filesha1 = Hasher.sha1(gulpfile)
            data = cache_file.read()

            if gulpfile in data and data[gulpfile]["sha1"] == filesha1:
                return data[gulpfile]["tasks"]

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
        process = CrossPlatformProcess(self.working_dir)
        (stdout, stderr) = process.run_sync(r'node "%s/write_tasks_to_cache.js"' % self.settings.package_path())

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
        process = CrossPlatformProcess(self.working_dir)
        (stdout, stderr) = process.run_sync(r'gulp -v')

        if process.failed or not GulpVersion(stdout).supports_tasks_simple():
            raise Exception("Gulp: Could not get the current gulp version or your gulp CLI version is lower than 3.7.0")

        (stdout, stderr) = process.run_sync(r'gulp --tasks-simple')

        gulpfile = self.get_gulpfile_path(self.working_dir)

        if not stdout:
            raise Exception("Gulp: The result of `gulp --tasks-simple` was empty")

        CacheFile(self.working_dir).write({
            gulpfile: {
                "sha1": Hasher.sha1(gulpfile),
                "tasks": dict((task, { "name": task, "dependencies": "" }) for task in stdout.split("\n") if task)
            }
        })

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
        process = CrossPlatformProcess(self.working_dir)
        process.run(task)
        stdout, stderr = process.communicate(self.append_to_output_view_in_main_thread)
        defer_sync(lambda: self.finish(stdout, stderr))

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
        if ProcessCache.last_command:
            task_name = ProcessCache.last_command.replace('gulp ', '').strip()
            self.window.run_command("gulp", { "task_name": task_name })
        else:
            self.status_message("You need to run a task first")


class GulpKillTaskCommand(BaseCommand):
    def work(self):
        ProcessCache.refresh()

        if ProcessCache.empty():
            self.status_message("There are no running tasks")
        else:
            self.procs = ProcessCache.get()
            quick_panel_list = [[process.last_command, process.working_dir, 'PID: %d' % process.pid] for process in self.procs]
            self.show_quick_panel(quick_panel_list, self.kill_process, font=0)

    def kill_process(self, index=-1):
        if index >= 0 and index < len(self.procs):
            process = self.procs[index]
            try:
                process.kill()
            except ProcessLookupError as e:
                print('Process %d seems to be dead already' % process.pid)

            self.show_output_panel('')
            self.append_to_output_view("\n%s killed! # %s | PID: %d\n" % process.to_tuple())


class GulpKillCommand(BaseCommand):
    def work(self):
        ProcessCache.refresh()

        if ProcessCache.empty():
            self.status_message("There are no running tasks")
        else:
            self.append_processes_to_output_view()
            ProcessCache.kill_all()
            self.append_to_output_view("\nAll running tasks killed!\n")

    def append_processes_to_output_view(self):
        self.show_output_panel("\nFinishing the following running tasks:\n")
        ProcessCache.each(lambda process: self.append_to_output_view("$ %s # %s | PID: %d\n" % process.to_tuple()))


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
        progress = ProgressNotifier("%s: Working" % Settings.PACKAGE_NAME)
        thread = PluginRegistryCall()
        thread.start()
        self.handle_thread(thread, progress)

    def handle_thread(self, thread, progress):
        if thread.is_alive() and not thread.error:
            set_timeout(lambda: self.handle_thread(thread, progress), 100)
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
                cache_file = CacheFile(self.working_dir)
                if cache_file.exists():
                    cache_file.remove()
                    self.status_message('Cache removed successfully')
            except Exception as e:
                self.status_message("Could not remove cache: %s" % str(e))


class GulpExitCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            self.window.run_command("gulp_kill")
        finally:
            self.window.run_command("exit")


def plugin_loaded():
    def load_process_cache():
        for process in ProcessCache.get_from_storage():
            ProcessCache.add(
                CrossPlatformProcess(process['workding_dir'], process['last_command'], process['pid'])
            )

    async(load_process_cache, 200, silent=True)


if not is_sublime_text_3:
    plugin_loaded()
