import sublime
import sublime_plugin
import os
from fnmatch import fnmatch

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
	from .settings import Settings
else:
	from settings import Settings

class EventTask(sublime_plugin.EventListener):
	def on_post_save(self, view):
		self.view = view
		self.run_tasks(Settings().get("tasks_on_save", {}))
		self.run_tasks(Settings().get("silent_tasks_on_save", {}), silent=True)

	def run_tasks(self, tasks_on_save, silent=False):
		if tasks_on_save:
			for key in tasks_on_save:
				value = tasks_on_save[key]
				if isinstance(value, list):
					for pattern in value:
						self.run(key, pattern, silent)
				else:
					self.run(key, value, silent)

	def run(self, task, pattern, silent):
		folders = self.view.window().folders() or []
		if any(fnmatch(self.view.file_name(), os.path.join(folder, pattern)) for folder in folders):
			self.view.window().run_command("gulp", { "task_name": task, "silent": silent })
