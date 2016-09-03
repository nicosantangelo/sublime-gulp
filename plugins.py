import sublime
from threading import Thread

is_sublime_text_3 = int(sublime.version()) >= 3000

if is_sublime_text_3:
    import urllib.request as urllib2
else:
    import urllib2


class PluginList():
    def __init__(self, plugins_response):
        self.plugins = [Plugin(plugin_json) for plugin_json in plugins_response["results"]]
        self.length = len(self.plugins)

    def get(self, index):
        if index >= 0 and index < self.length:
            return self.plugins[index]

    def quick_panel_list(self):
        return [ [plugin.name + ' (' + plugin.version + ')', plugin.description] for plugin in self.plugins ]


class Plugin():
    def __init__(self, plugin_json):
        self.plugin = plugin_json
        self.set_attributes()

    def set_attributes(self):
        self.name = self.get('name')
        self.version = "v" + self.get('version')
        self.description = self.get('description')

    def get(self, property):
        return self.plugin[property][0] if self.has(property) else ''

    def has(self, property):
        return property in self.plugin


class PluginRegistryCall(Thread):
    url = "http://npmsearch.com/query?fields=name,description,homepage,version,rating&q=keywords:gulpfriendly&q=keywords:gulpplugin&size=1755&sort=rating:desc&start=20"

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.result = None
        self.error = None
        Thread.__init__(self)

    def run(self):
        try:
            request = urllib2.Request(self.url, None, headers={ "User-Agent": "Sublime Text" })
            http_file = urllib2.urlopen(request, timeout=self.timeout)
            self.result = http_file.read()
            return

        except urllib2.HTTPError as e:
            err = 'Error: HTTP error %s contacting gulpjs registry' % (str(e.code))
        except urllib2.URLError as e:
            err = 'Error: URL error %s contacting gulpjs registry' % (str(e.reason))

        self.error = err
        self.result = None
