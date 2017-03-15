import shlex
import subprocess
import threading
import yaml

import lock

DEFAULT_TIMEOUT = 600


class JobWrapper(object):
    def __init__(self, conf_file):
        self.config = yaml.safe_load(file(conf_file, "r"))
        self.name = self.config["name"]
        lock.begin()

    def run(self):
        command = shlex.split(self.config["command"])

        if "timeout" in self.config:
            timeout = self.config["timeout"]
        else:
            timeout = DEFAULT_TIMEOUT

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = threading.Timer(timeout, process.kill)

        try:
            # FIXME: This doesn't stream, so large output will be buffered in memory.
            (stdout_data, stderr_data) = process.communicate()
        finally:
            timer.cancel()
            lock.end()
