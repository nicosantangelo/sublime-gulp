import sublime

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    from .settings import Settings
    from .progress_notifier import ProgressNotifier
else:
    from settings import Settings
    from progress_notifier import ProgressNotifier


def defer_sync(fn):
    set_timeout(fn, 0)

def defer(fn):
    async(fn, 0)

def async(fn, delay, silent=False):
    if is_sublime_text_3:
        if silent:
            sublime.set_timeout_async(fn, delay)
        else:
            progress = ProgressNotifier("%s: Working" % Settings.PACKAGE_NAME)
            sublime.set_timeout_async(lambda: call(fn, progress), delay)
    else:
        set_timeout(fn, delay)

def set_timeout(fn, delay):
    sublime.set_timeout(fn, delay)

def call(fn, progress):
    fn()
    progress.stop()
