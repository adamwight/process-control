'''
Lockfile using a temporary file and the process id.

Self-corrects stale locks unless "failopen" is True.
'''
from __future__ import print_function
import os
import os.path
import sys

lockfile = None


def begin(filename=None, failopen=False, job_tag=None):
    if not filename:
        filename = "/tmp/{name}.lock".format(name=job_tag)

    if os.path.exists(filename):
        print("Lockfile found!", file=sys.stderr)
        f = open(filename, "r")
        pid = None
        try:
            pid = int(f.read())
        except ValueError:
            pass
        f.close()
        if not pid:
            print("Invalid lockfile contents.", file=sys.stderr)
        else:
            try:
                os.getpgid(pid)
                raise LockError("Aborting! Previous process ({pid}) is still alive. Remove lockfile manually if in error: {path}".format(pid=pid, path=filename))
            except OSError:
                if failopen:
                    raise LockError("Aborting until stale lockfile is investigated: {path}".format(path=filename))
                print("Lockfile is stale.", file=sys.stderr)
        print("Removing old lockfile.", file=sys.stderr)
        os.unlink(filename)

    f = open(filename, "w")
    f.write(str(os.getpid()))
    f.close()

    global lockfile
    lockfile = filename


def end():
    global lockfile
    if lockfile and os.path.exists(lockfile):
        os.unlink(lockfile)
    else:
        raise LockError("Already unlocked!")


class LockError(RuntimeError):
    pass
