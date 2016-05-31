"""
hashdir based on: https://github.com/cakepietoast/checksumdir
"""

import os
import hashlib
import re


class Hasher():
    @classmethod
    def sha1(self, filepath):
        return self.hashdir(filepath) if os.path.isdir(filepath) else self.hashfile(filepath)

    @classmethod
    def hashfile(self, filepath):
        filehash = hashlib.sha1()
        with open(filepath, mode='rb') as f:
            content = f.read()
            filehash.update(str("blob " + str(len(content)) + "\0").encode('UTF-8'))
            filehash.update(content)
        return filehash.hexdigest()

    @classmethod
    def hashdir(self, dirpath):
        hashvalues = []
        for root, dirs, files in os.walk(dirpath, topdown=True):
            if not re.search(r'/\.', root):
                values = [self._dirfilehash(os.path.join(root, f)) for f in files if not f.startswith('.') and not re.search(r'/\.', f)]
                hashvalues.extend(values)
        return self._reducehash(hashvalues)

    @classmethod
    def _dirfilehash(self, filepath):
        hasher = hashlib.sha1()
        blocksize = 64 * 1024
        with open(filepath, 'rb') as fp:
            while True:
                data = fp.read(blocksize)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()

    @classmethod
    def _reducehash(self, hashlist):
        hasher = hashlib.sha1()
        for hashvalue in sorted(hashlist):
            hasher.update(hashvalue.encode('utf-8'))
        return hasher.hexdigest()
