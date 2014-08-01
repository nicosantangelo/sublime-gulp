import sublime, sublime_plugin

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .progress_notifier import ProgressNotifier
else:
    from progress_notifier import ProgressNotifier

# A base for each command
class BaseCommand(sublime_plugin.WindowCommand):
    def run(self, task_name = None):
        self.setup_data_from_settings()
        self.task_name = task_name
        self.work()

    def setup_data_from_settings(self):
        self.settings = sublime.load_settings("Gulp.sublime-settings")

    # Main method, override
    def work(self):
        pass

    # Panels and message
    def display_message(self, text):
        sublime.active_window().active_view().set_status("gulp", text)

    def show_quick_panel(self, items, on_done = None, font = sublime.MONOSPACE_FONT):
        self.defer_sync(lambda: self.window.show_quick_panel(items, on_done, font))

    def show_input_panel(self, caption, initial_text = "", on_done = None, on_change = None, on_cancel = None):
        self.window.show_input_panel(caption, initial_text, on_done, on_change, on_cancel)

    # Output view
    def show_output_panel(self, text):
        if self.settings.get("results_in_new_tab", False):
            self.output_view = self.window.open_file("Gulp Results")
        else:
            self.output_view = self.window.get_output_panel("gulp_output")
            self.window.run_command("show_panel", { "panel": "output.gulp_output" })
            
        self.output_view.settings().set("scroll_past_end", False)
        self.add_syntax()
        self.append_to_output_view(text)

    def add_syntax(self):
        syntax_file = self.settings.get("syntax", "Packages/Gulp/syntax/GulpResults.tmLanguage")
        if syntax_file:
            self.output_view.set_syntax_file(syntax_file)

    def append_to_output_view(self, text):
        self.output_view.set_read_only(False)
        self._insert(self.output_view, CrossPlaformCodecs.decode(text))
        self.output_view.set_read_only(True)

    def _insert(self, view, content):
        view.run_command("view_insert", { "size": view.size(), "content": content })
        view.set_viewport_position((0, view.size()), True)

    # Async calls
    def defer_sync(self, fn):
        sublime.set_timeout(fn, 0)

    def defer(self, fn):
        self.async(fn, 0)
        
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