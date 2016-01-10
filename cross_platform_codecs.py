import sublime
import sys
import re

class CrossPlaformCodecs():
    @classmethod
    def decode_line(self, line):
        line = line.rstrip()
        decoded_line = self.force_decode(line) if sys.version_info >= (3, 0) else line
        decoded_line = decoded_line.lstrip('\n\r')
        decoded_line = re.sub(r'\033\[(\d{1,2}m|\d\w)', '', str(decoded_line))
        return decoded_line + "\n"

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

    @classmethod
    def encode_process_command(self, command):
        is_sublime_2_and_in_windows = sublime.platform() == "windows" and int(sublime.version()) < 3000
        return command.encode(sys.getfilesystemencoding()) if is_sublime_2_and_in_windows else command