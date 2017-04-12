'''
Lockfile using a temporary file and the process id.

Self-corrects stale locks unless "failopen" is True.
'''
import os

from processcontrol import config


lockfile = None


def path_for_job(job_name):
    run_dir = config.GlobalConfiguration().get("run_directory")
    filename = "{run_dir}/{name}.lock".format(run_dir=run_dir, name=job_name)
    return filename


# TODO: Decide whether we want to failopen?
def begin(failopen=False, slug=None):
    filename = path_for_job(slug)

    if os.path.exists(filename):
        config.log.error("Lockfile found!")
        with open(filename, "r") as f:
            pid = None
            try:
                pid = int(f.read())
            except ValueError:
                pass

        if not pid:
            config.log.error("Invalid lockfile contents.")
        else:
            try:
                os.getpgid(pid)
                raise LockError("Aborting! Previous process ({pid}) is still alive. Remove lockfile manually if in error: {path}".format(pid=pid, path=filename))
            except OSError:
                if failopen:
                    raise LockError("Aborting until stale lockfile is investigated: {path}".format(path=filename))
                config.log.error("Lockfile is stale.")
        config.log.error("Removing old lockfile.")
        os.unlink(filename)

    with open(filename, "w") as f:
        config.log.debug("Writing lockfile.")
        f.write(str(os.getpid()))

    global lockfile
    lockfile = filename


def end():
    global lockfile
    if lockfile:
        if os.path.exists(lockfile):
            config.log.debug("Clearing lockfile.")
            os.unlink(lockfile)
        else:
            raise LockError("Already unlocked!")

    lockfile = None


class LockError(RuntimeError):
    pass
