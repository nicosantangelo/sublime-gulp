import sublime
import sublime_plugin
import os.path

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .settings import Settings
    from .insert_in_output_view import insert_in_output_view
    from .timeout import set_timeout, defer_sync
else:
    from settings import Settings
    from insert_in_output_view import insert_in_output_view
    from timeout import set_timeout, defer_sync


#
# A base for each command
#

class BaseCommand(sublime_plugin.WindowCommand):
    def run(self, task_name=None, task_flag=None, silent=False, paths=[]):
        self.setup_data_from_settings()
        self.task_name = task_name
        self.task_flag = task_flag if task_name is not None and task_flag is not None else self.get_flag_from_task_name()
        self.silent = silent
        self._working_dir = ""
        self.sercheable_folders = [os.path.dirname(path) for path in paths] if len(paths) > 0 else self.window.folders()
        self.output_view = None
        self.work()

    def setup_data_from_settings(self):
        Settings.gather_shared_data()
        self.settings = Settings()
        self.results_in_new_tab = self.settings.get("results_in_new_tab", False)
        self.check_for_gulpfile = self.settings.get('check_for_gulpfile', True)

    def get_flag_from_task_name(self):
        flags = self.settings.get("flags", {})
        return flags[self.task_name] if self.task_name in flags else ""

    # Properties
    @property
    def working_dir(self):
        return self._working_dir

    @working_dir.setter
    def working_dir(self, value):
        if self.check_for_gulpfile:
            self._working_dir = os.path.dirname(value)
        else:
            self._working_dir = value

    # Main method, override
    def work(self):
        pass

    # Panels and message
    def show_quick_panel(self, items, on_done=None, font=sublime.MONOSPACE_FONT):
        defer_sync(lambda: self.window.show_quick_panel(items, on_done, font))

    def show_input_panel(self, caption, initial_text="", on_done=None, on_change=None, on_cancel=None):
        self.window.show_input_panel(caption, initial_text, on_done, on_change, on_cancel)

    def status_message(self, text):
        sublime.status_message("%s: %s" % (Settings.PACKAGE_NAME, text))

    def error_message(self, text):
        sublime.error_message("%s: %s" % (Settings.PACKAGE_NAME, text))

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
        return next(folder_path for folder_path in self.sercheable_folders if self.working_dir.find(folder_path) != -1) if self.working_dir else ""

    def gulp_results_view(self):
        if self.output_view is None:
            gulp_results = [view for view in sublime.active_window().views() if view.file_name() and os.path.basename(view.file_name()) == "Gulp Results"]
            return gulp_results[0] if len(gulp_results) > 0 else None
        else:
            return self.output_view

    def add_syntax(self):
        if self.settings.has("syntax_override"):
            syntax_file = self.settings.get("syntax_override")
        else:
            syntax_file = self.settings.get_from_user_settings("syntax", "Packages/Gulp/syntax/GulpResults.tmLanguage")

        if syntax_file:
            self.output_view.set_syntax_file(syntax_file)

    def append_to_output_view_in_main_thread(self, text):
        defer_sync(lambda: self.append_to_output_view(text))

    def append_to_output_view(self, text):
        if not self.silent:
            insert_in_output_view(self.output_view, text, self.results_in_new_tab)

    def set_output_close_on_timeout(self):
        timeout = self.settings.get("results_autoclose_timeout_in_milliseconds", False)
        if timeout:
            set_timeout(self.close_panel, timeout)

    def close_panel(self):
        if self.results_in_new_tab:
            self.output_view = self.gulp_results_view()
            if self.output_view and self.output_view.file_name():
                self.window.focus_view(self.output_view)
                self.window.run_command('close_file')
        else:
            self.window.run_command("hide_panel", { "panel": "output.gulp_output" })

    def show_panel(self):
        self.window.run_command("show_panel", { "panel": "output.gulp_output" })
