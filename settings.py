import sublime


class Settings():
    def __init__(self):
        active_view = sublime.active_window().active_view()
        self.user_settings = sublime.load_settings("Gulp.sublime-settings")
        self.sources = [active_view.settings(), ProjectData(), self.user_settings]

    def get(self, key, default=None):
        return next((settings.get(key, default) for settings in self.sources if settings.has(key)), None)

    def get_from_user_settings(self, key, default=None):
        return self.user_settings.get(key, default)

    def has(self, key):
        return any(settings.has(key) for settings in self.sources)


class ProjectData():
    def __init__(self):
        self._project_data = sublime.active_window().project_data().get('Gulp', {}) if int(sublime.version()) >= 3000 else {}

    def get(self, key, default):
        return self._project_data.get(key, default)

    def has(self, key):
        return key in self._project_data
