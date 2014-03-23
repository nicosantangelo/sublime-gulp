import sublime, sublime_plugin, re

# A base for each command
class BaseCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.setup_data_from_settings()
        self.work(edit)

    def setup_data_from_settings(self):
        self.settings = sublime.load_settings("Gulp.sublime-settings")

    # Main method, override
    def work(self, edit):
        pass

    # Panels and message
    def display_message(self, text):
        sublime.active_window().active_view().set_status("gulp", text)

    def show_quick_panel(self, items, on_done = None, on_highlighted = None, selected_index = -1):
        sublime.set_timeout(lambda: self.view.window().show_quick_panel(items, on_done, sublime.MONOSPACE_FONT, selected_index, on_highlighted), 0)

    def show_input_panel(self, caption, initial_text = "", on_done = None, on_change = None, on_cancel = None):
        self.view.window().show_input_panel(caption, initial_text, on_done, on_change, on_cancel)

    # Output view
    def show_in_editable_tab(self, text, extra = None):
        view = self.show_in_tab(text)
        view.set_scratch(True)
        OpenViews.set(view, extra)

    def show_in_tab(self, text):
        view = self.view.window().new_file()
        view.set_name("Gulp")
        view.run_command("view_insert", { "size" : view.size(), "content": text });
        self.set_new_view_attributes(view)
        return view

    def show_output_panel(self, text):
        self.output_view = self.view.window().get_output_panel("textarea")
        self.append_to_output_view(text)
        self.view.window().run_command("show_panel", { "panel": "output.textarea" })
        self.set_new_view_attributes(self.output_view)

    def append_to_output_view(self, text):
        self.output_view.set_read_only(False)
        self.output_view.run_command("append", { "characters": text })
        self.output_view.set_read_only(True)

    def set_new_view_attributes(self, view):
        view.set_syntax_file(self.syntax_file)
        view.set_viewport_position((0, 0), True)

class ViewInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, size, content):
        self.view.insert(edit, size, content)