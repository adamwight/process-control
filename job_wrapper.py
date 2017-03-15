import shlex
import subprocess
import threading
import yaml

import lock

DEFAULT_TIMEOUT = 600


class JobWrapper(object):
    def __init__(self, config_path=None):
        self.config = yaml.safe_load(file(config_path, "r"))
        self.name = self.config["name"]
        lock.begin(job_tag=self.name)

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
