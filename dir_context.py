import os
from contextlib import contextmanager


class Dir():
    @classmethod
    @contextmanager
    def cd(cls, newdir):
        prevdir = os.getcwd()
        os.chdir(newdir)
        try:
            yield
        finally:
            os.chdir(prevdir)
