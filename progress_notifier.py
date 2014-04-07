# Adapted from Will Bonds Package Control (thread_progress.py)
import sublime

class ProgressNotifier():
    """
    Animates an indicator, [=   ]

    :param message:
        The message to display next to the activity indicator

    :param success_message:
        The message to display once the thread is complete
    """

    def __init__(self, message, success_message = ''):
        self.message = message
        self.success_message = success_message
        self.stopped = False
        self.addend = 1
        self.size = 8
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if self.stopped:
            return

        before = i % self.size
        after = (self.size - 1) - before

        sublime.status_message('%s [%s=%s]' % (self.message, ' ' * before, ' ' * after))

        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend

        sublime.set_timeout(lambda: self.run(i), 100)

    def stop(self):
        sublime.status_message(self.success_message)
        self.stopped = True