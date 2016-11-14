import sublime
import os.path

is_sublime_text_3 = int(sublime.version()) >= 3000


class Settings():
    PACKAGE_NAME = "Gulp"
    PACKAGE_SETTINGS = "Gulp.sublime-settings"
    CACHE_FILE_NAME = ".sublime-gulp.cache"

    SHARED_DATA = {}

    @classmethod
    def package_path(cls):
        return os.path.join(sublime.packages_path(), Settings.PACKAGE_NAME)

    @classmethod
    def gather_shared_data(cls):
        settings = Settings()
        Settings.SHARED_DATA = ProjectData({
            'track_processes': settings.get("track_processes", True),
            'nonblocking': settings.get("nonblocking", True),
            'exec_args': settings.get("exec_args", False)
        })

    @classmethod
    def get_from_shared_data(cls, key, default=None):
        return Settings.SHARED_DATA.get(key, default)

    def __init__(self):
        self.user_settings = sublime.load_settings(Settings.PACKAGE_SETTINGS)
        self.sources = [ProjectData(), self.user_settings]

        active_view = sublime.active_window().active_view()
        if active_view:
            self.sources.append(active_view.settings())

    def get(self, key, default=None):
        return next((settings.get(key, default) for settings in self.sources if settings.has(key)), None)

    def get_from_user_settings(self, key, default=None):
        return self.user_settings.get(key, default)

    def has(self, key):
        return any(settings.has(key) for settings in self.sources)


class ProjectData():
    def __init__(self, data=None):
        if data is not None:
            self._project_data = data
        else:
            active_window = sublime.active_window()
            if is_sublime_text_3 and active_window:
                self._project_data = active_window.project_data().get(Settings.PACKAGE_NAME, {})
            else:
                self._project_data = {}


    def get(self, key, default):
        return self._project_data.get(key, default)

    def has(self, key):
        return key in self._project_data
