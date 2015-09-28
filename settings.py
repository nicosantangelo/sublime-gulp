import sublime

class Settings():
    def __init__(self):
        active_view = sublime.active_window().active_view()
        self._sources = [active_view.settings(), ProjectData(), sublime.load_settings("Gulp.sublime-settings")]

    def get(self, key, default=False):
        return next((settings.get(key, default) for settings in self._sources if settings.has(key)), None)


class ProjectData():
    def __init__(self):
        self._project_data = sublime.active_window().project_data().get('Gulp', {}) if int(sublime.version()) >= 3000 else {}

    def get(self, key, default):
        return self._project_data.get(key, default)

    def has(self, key):
        return key in self._project_data