import sublime, sublime_plugin
import os.path

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .progress_notifier import ProgressNotifier
else:
    from progress_notifier import ProgressNotifier

# A base for each command
class BaseCommand(sublime_plugin.WindowCommand):
    package_name = "Gulp"
    
    def run(self, task_name = None, task_flag = None, silent = False):
        self.setup_data_from_settings()
        self.task_name = task_name
        self.task_flag = task_flag if task_name and task_flag is not None else self.get_flag_from_task_name()
        self.silent = silent
        self.working_dir = ""
        self.work()

    def setup_data_from_settings(self):
        self.settings = sublime.load_settings("Gulp.sublime-settings")
        self.results_in_new_tab = self.settings.get("results_in_new_tab", False)
        self.nonblocking  = self.settings.get("nonblocking", True)

    def get_flag_from_task_name(self):
        flags = self.settings.get("flags", {})
        return flags[self.task_name] if self.task_name in flags else ""

    # Main method, override
    def work(self):
        pass

    # Panels and message
    def show_quick_panel(self, items, on_done = None, font = sublime.MONOSPACE_FONT):
        self.defer_sync(lambda: self.window.show_quick_panel(items, on_done, font))

    def show_input_panel(self, caption, initial_text = "", on_done = None, on_change = None, on_cancel = None):
        self.window.show_input_panel(caption, initial_text, on_done, on_change, on_cancel)

    def status_message(self, text):
        sublime.status_message("%s: %s" % (self.package_name, text))

    def error_message(self, text):
        sublime.error_message("%s: %s" % (self.package_name, text))

    # Output view
    def show_output_panel(self, text):
        if self.silent:
            self.status_message(text)
            return
        
        if self.results_in_new_tab:
            new_tab_path = os.path.join(self.gulp_results_path(), "Gulp Results")
            self.output_view = self.window.open_file(new_tab_path)
            self.output_view.set_scratch(True)
        else:
            self.output_view = self.window.get_output_panel("gulp_output")
            self.show_panel()
            
        self.output_view.settings().set("scroll_past_end", False)
        self.add_syntax()
        self.append_to_output_view(text)

    def gulp_results_path(self):
        return next(folder_path for folder_path in self.window.folders() if self.working_dir.find(folder_path) != -1) if self.working_dir else ""

    def add_syntax(self):
        syntax_file = self.settings.get("syntax", "Packages/Gulp/syntax/GulpResults.tmLanguage")
        if syntax_file:
            self.output_view.set_syntax_file(syntax_file)

    def append_to_output_view_in_main_thread(self, text):
        self.defer_sync(lambda: self.append_to_output_view(text))

    def append_to_output_view(self, text):
        if not self.silent:
            self._insert(self.output_view, CrossPlaformCodecs.decode(text))

    def _insert(self, view, content):
        if self.results_in_new_tab and self.output_view.is_loading():
            self.set_timeout(lambda: self._insert(view, content), 10)
        else:
            view.set_read_only(False)
            view.run_command("view_insert", { "size": view.size(), "content": content })
            view.set_viewport_position((0, view.size()), True)
            view.set_read_only(True)

    def set_output_close_on_timeout(self):
        timeout = self.settings.get("results_autoclose_timeout_in_milliseconds", False)
        if timeout:
            self.set_timeout(self.close_panel, timeout)

    def close_panel(self):
        if self.results_in_new_tab:
            self.window.focus_view(self.output_view)
            self.window.run_command('close_file')
        else:
            self.window.run_command("hide_panel", { "panel": "output.gulp_output" })

    def show_panel(self):
        self.window.run_command("show_panel", { "panel": "output.gulp_output" })

    # Sync/async calls
    def defer_sync(self, fn):
        self.set_timeout(fn, 0)

    def defer(self, fn):
        self.async(fn, 0)

    def set_timeout(self, fn, delay):
        sublime.set_timeout(fn, delay)
        
    def async(self, fn, delay):
        if is_sublime_text_3:
            progress = ProgressNotifier('Gulp: Working')
            sublime.set_timeout_async(lambda: self.call(fn, progress), delay)
        else:
            fn()

    def call(self, fn, progress):
        fn()
        progress.stop()

class CrossPlaformCodecs():
    @classmethod
    def decode(self, text):
        return text if is_sublime_text_3 else text.decode('utf-8')

class ViewInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, size, content):
        self.view.insert(edit, int(size), content)