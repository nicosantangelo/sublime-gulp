import re

# Workaround for Windows ST2 not having disutils
try:
    from distutils.version import LooseVersion
except:
    # From distutils/version.py
    class LooseVersion():
        component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)

        def __init__ (self, vstring=None):
            if vstring:
                self.parse(vstring)

        def __ge__(self, other):
            c = self._cmp(other)
            if c is NotImplemented:
                return c
            return c >= 0

        def parse (self, vstring):
            self.vstring = vstring
            components = [x for x in self.component_re.split(vstring) if x and x != '.']
            for i, obj in enumerate(components):
                try:
                    components[i] = int(obj)
                except ValueError:
                    pass

            self.version = components

        def _cmp (self, other):
            if isinstance(other, str):
                other = LooseVersion(other)

            if self.version == other.version:
                return 0
            if self.version < other.version:
                return -1
            if self.version > other.version:
                return 1

#
# Actual class
#


class GulpVersion():
    def __init__(self, version_string):
        self.version_string = version_string or ""

    def supports_tasks_simple(self):
        return LooseVersion(self.cli_version()) >= LooseVersion("3.7.0")

    def cli_version(self):
       return self.get("CLI")

    def local_version(self):
        return self.get("Local")

    def get(self, version_name):
        re_match = re.search(version_name + " version (\d+\.\d+\.\d+)", self.version_string)
        return re_match.group(1) if re_match else "3.6.0"
