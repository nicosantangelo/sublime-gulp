import sublime, sublime_plugin, re

# A base for each command
class BaseCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.setup_data_from_settings()
        self.work()

    def setup_data_from_settings(self):
        self.settings = sublime.load_settings("Gulp.sublime-settings")

    # Main method, override
    def work(self):
        pass

    # Panels and message
    def display_message(self, text):
        sublime.active_window().active_view().set_status("gulp", text)

    def show_quick_panel(self, items, on_done = None):
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done, sublime.MONOSPACE_FONT), 0)

    def show_input_panel(self, caption, initial_text = "", on_done = None, on_change = None, on_cancel = None):
        self.window.show_input_panel(caption, initial_text, on_done, on_change, on_cancel)

    # Output view
    def show_in_tab(self, text):
        view = self.window.new_file() 
        view.set_name("Gulp")
        self._insert(view, text)
        return view

    # Use this method and check the conditional here. open_file or get_output_panel
    def show_output_panel(self, text):
        self.output_view = self.window.get_output_panel("gulp_output")
        self.append_to_output_view(text)
        self.window.run_command("show_panel", { "panel": "output.gulp_output" })

    def append_to_output_view(self, text):
        self.output_view.set_read_only(False)
        self._insert(self.output_view, text, True)
        self.output_view.set_read_only(True)

    def _insert(self, view, content, scroll_to_end = False):
        view.run_command("view_insert", { "size": view.size(), "content": content })
        position = (view.size(), view.size()) if scroll_to_end else (0, 0)
        view.set_viewport_position(position, True)

class ViewInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, size, content):
        self.view.insert(edit, size, content)