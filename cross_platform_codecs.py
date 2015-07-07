import sys

class CrossPlaformCodecs():
    @classmethod
    def decode_line(self, line):
        line = line.rstrip()
        decoded_line = self.force_decode(line) if sys.version_info >= (3, 0) else line
        return str(decoded_line) + "\n"

    @classmethod
    def force_decode(self, text):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            if sublime.platform() == "windows":
                text = self.decode_windows_line(text)
        return text

    @classmethod
    def decode_windows_line(self, text):
        # Import only for Windows
        import locale, subprocess

        # STDERR gets the wrong encoding, use chcp to get the real one
        proccess = subprocess.Popen(["chcp"], shell=True, stdout=subprocess.PIPE)
        (chcp, _) = proccess.communicate()

        # Decode using the locale preferred encoding (for example 'cp1251') and remove newlines
        chcp = chcp.decode(locale.getpreferredencoding()).strip()

        # Get the actual number
        chcp = chcp.split(" ")[-1]

        # Actually decode
        return text.decode("cp" + chcp)