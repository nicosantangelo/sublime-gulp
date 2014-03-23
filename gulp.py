try:
    from .base_command import BaseCommand
except ImportError:
    from base_command import BaseCommand

class GulpCommand(BaseCommand):
    def work(self, edit):
        self.show_quick_panel(["task"])
