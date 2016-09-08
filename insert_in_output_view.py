import sublime
import sublime_plugin

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .cross_platform_codecs import CrossPlatformCodecs
    from .timeout import set_timeout
else:
    from cross_platform_codecs import CrossPlatformCodecs
    from timeout import set_timeout


def insert_in_output_view(view, content, in_new_tab):
    if view is None:
        return

    if in_new_tab and view.is_loading():
        set_timeout(lambda: insert_in_output_view(view, content, in_new_tab), 10)
    else:
        decoded_contenet = content if is_sublime_text_3 else CrossPlatformCodecs.force_decode(content)

        view.set_read_only(False)
        view.run_command("view_insert", { "size": view.size(), "content": decoded_contenet })
        view.set_viewport_position((0, view.size()), True)
        view.set_read_only(True)


class ViewInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, size, content):
        self.view.insert(edit, int(size), content)
