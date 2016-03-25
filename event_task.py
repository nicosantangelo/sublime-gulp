import sublime
import sublime_plugin
import fnmatch
import os

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
	from .settings import Settings
else:
	from settings import Settings

class EventTask(sublime_plugin.EventListener):

	def on_post_save(self, view):
		task_on_save = Settings().get("tasks_on_save", {})
		if task_on_save is not None:
			for key in task_on_save:
				value = task_on_save[key]
				if isinstance(value, str):
					self.run(view, key, value)
				elif isinstance(value, list):
					for pattern in value:
						self.run(view, key, pattern)

	def run(self, view, task, pattern):
		folders = view.window().folders()
		pattern = folders[0] + os.sep + pattern if folders else ""
		if fnmatch.fnmatch(view.file_name(), pattern):
			view.window().run_command("gulp", {"task_name": task})
