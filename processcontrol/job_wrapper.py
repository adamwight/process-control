from __future__ import print_function
import datetime
import shlex
import subprocess
import sys
import threading

from . import config
from . import lock
from . import mailer

# FIXME: move to global config
DEFAULT_TIMEOUT = 600


class JobWrapper(object):
    def __init__(self, config_path=None):
        self.global_config = config.GlobalConfiguration()
        self.config_path = config_path
        self.config = config.JobConfiguration(self.global_config, self.config_path)

        self.name = self.config.get("name")
        self.start_time = datetime.datetime.utcnow().isoformat()
        self.mailer = mailer.Mailer(self.config)

        if self.config.has("timeout"):
            self.timeout = self.config.get("timeout")
        else:
            self.timeout = DEFAULT_TIMEOUT

        if self.config.has("disabled") and self.config.get("disabled") is True:
            self.enabled = False
        else:
            self.enabled = True

        if not self.config.has("schedule"):
            self.enabled = False

    def run(self):
        lock.begin(job_tag=self.name)

        command = shlex.split(self.config.get("command"))

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = threading.Timer(self.timeout, self.fail_timeout)
        timer.start()

        try:
            # FIXME: This doesn't stream, so large output will be buffered in memory.
            (stdout_data, stderr_data) = self.process.communicate()

            self.store_job_output(stdout_data)

            if len(stderr_data) > 0:
                self.fail_has_stderr(stderr_data)
        finally:
            timer.cancel()
            lock.end()

        return_code = self.process.returncode
        if return_code != 0:
            self.fail_exitcode(return_code)

    def fail_exitcode(self, return_code):
        message = "Job {name} failed with code {code}".format(name=self.name, code=return_code)
        print(message, file=sys.stderr)
        # TODO: Prevent future jobs according to config.
        self.mailer.fail_mail(message)

    def fail_has_stderr(self, stderr_data):
        message = "Job {name} printed things to stderr:".format(name=self.name)
        print(message, file=sys.stderr)
        body = stderr_data.decode("utf-8")
        print(body, file=sys.stderr)
        self.mailer.fail_mail(message, body)

    def fail_timeout(self):
        self.process.kill()
        message = "Job {name} timed out after {timeout} seconds".format(name=self.name, timeout=self.timeout)
        print(message, file=sys.stderr)
        self.mailer.fail_mail(message)
        # FIXME: Job will return SIGKILL now, fail_exitcode should ignore that signal now?

    def store_job_output(self, stdout_data):
        if not self.config.has("stdout_destination"):
            return

        destination = self.config.get("stdout_destination")
        out = open(destination, "a")

        header = (
            "===========\n"
            "{name} ({pid}), started at {time}\n"
            "-----------\n"
        ).format(name=self.name, pid=self.process.pid, time=self.start_time)
        print(header, file=out)

        out.write(stdout_data.decode("utf-8"))
