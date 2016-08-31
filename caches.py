import sublime
import json
import codecs
import os


class ProcessCache():
    _procs = []
    last_command = None

    @classmethod
    def copy(cls):
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
        cls._procs.append(process)
        cls._cache().update(lambda procs: procs + [process.to_json()])

    @classmethod
    def remove(cls, process):
        if process in cls._procs:
            cls._procs.remove(process)
        cls._cache().update(lambda procs: [proc for proc in procs if proc['pid'] != process.pid])

    @classmethod
    def kill_all(cls):
        cls.each(lambda process: process.kill())
        cls.clear()

    @classmethod
    def each(cls, fn):
        # for process_json in cls.cache().read():
        #     fn(Process(process_json))
        for process in cls.copy():
            fn(process)

    @classmethod
    def empty(cls):
        return len(cls._procs) == 0
        # return len(cls.cache().read()) == 0

    @classmethod
    def clear(cls):
        del cls._procs[:]
        cls.cache().write([])

    @classmethod
    def _cache(cls):
        return CacheFile(os.path.join(sublime.packages_path(), "Gulp"))


class CacheFile():
    cache_file_name = ".sublime-gulp.cache"

    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.cache_path = os.path.join(self.working_dir, CacheFile.cache_file_name)

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
