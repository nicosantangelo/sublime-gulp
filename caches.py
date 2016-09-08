import sublime
import json
import codecs
import os

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .settings import Settings
else:
    from settings import Settings


class ProcessCache():
    _procs = []
    last_command = None

    @classmethod
    def get_from_storage(cls):
        return cls.storage().read() or []

    @classmethod
    def get(cls):
        return cls._procs[:]

    @classmethod
    def refresh(cls):
        def remove_dead(process):
            if not process.is_alive():
                cls.remove(process)
        cls.each(remove_dead)

    @classmethod
    def add(cls, process):
        cls.last_command = process.last_command
        if process not in cls._procs:
            cls._procs.append(process)

        process = process.to_json()
        cls.storage().update(lambda procs: procs + [process] if process not in procs else procs)

    @classmethod
    def remove(cls, process):
        if process in cls._procs:
            cls._procs.remove(process)
        cls.storage().update(lambda procs: [proc for proc in procs if proc['pid'] != process.pid])

    @classmethod
    def kill_all(cls):
        cls.each(lambda process: process.kill())
        cls.clear()

    @classmethod
    def each(cls, fn):
        for process in cls.get():
            fn(process)

    @classmethod
    def empty(cls):
        return len(cls._procs) == 0

    @classmethod
    def clear(cls):
        del cls._procs[:]
        cls.storage().write([])

    @classmethod
    def storage(cls):
        if Settings.get_from_shared_data("track_processes", True):
            return CacheFile(Settings.package_path()) 
        else:
            return Cache()


class Cache():
    def exists(self):
        pass

    def remove(self):
        pass

    def open(self, mode="r"):
        pass

    def read(self):
        pass

    def write(self, data):
        pass

    def update(self, fn):
        pass


class CacheFile(Cache):
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.cache_path = os.path.join(self.working_dir, Settings.CACHE_FILE_NAME)

    def exists(self):
        return os.path.exists(self.cache_path)

    def remove(self):
        return os.remove(self.cache_path)

    def open(self, mode="r"):
        return codecs.open(self.cache_path, mode, "utf-8", errors='replace')

    def read(self):
        data = None
        cache_file = self.open()
        try:
            data = json.load(cache_file)
        finally:
            cache_file.close()
        return data

    def write(self, data):
        cache_file = self.open("w")
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            cache_file.write(json_data)
        finally:
            cache_file.close()

    def update(self, fn):
        cache_file = codecs.open(self.cache_path, "r+", "utf-8", errors='replace')
        try:
            current_data = json.load(cache_file)
            cache_file.seek(0)

            new_data = fn(current_data)
            cache_file.write(json.dumps(new_data))
            cache_file.truncate()
        finally:
            cache_file.close()
