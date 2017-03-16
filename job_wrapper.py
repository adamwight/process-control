from __future__ import print_function
import datetime
import shlex
import subprocess
import sys
import threading
import yaml

import lock


# TODO: Global config.
DEFAULT_TIMEOUT = 600


class JobWrapper(object):
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = yaml.safe_load(open(config_path, "r"))
        self.validate_config()

        self.name = self.config["name"]
        self.start_time = datetime.datetime.utcnow().isoformat()

        if "timeout" in self.config:
            self.timeout = self.config["timeout"]
        else:
            self.timeout = DEFAULT_TIMEOUT

        if "disabled" in self.config and self.config["disabled"] is True:
            self.enabled = False
        else:
            self.enabled = True

        if "schedule" not in self.config:
            self.enabled = False

    def run(self):
        lock.begin(job_tag=self.name)

        command = shlex.split(self.config["command"])

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
        print("Job {name} failed with code {code}".format(name=self.name, code=return_code), file=sys.stderr)
        # TODO: Prevent future jobs according to config.

    def fail_has_stderr(self, stderr_data):
        print("Job {name} printed things to stderr:".format(name=self.name), file=sys.stderr)
        print(stderr_data.decode("utf-8"), file=sys.stderr)

    def fail_timeout(self):
        self.process.kill()
        print("Job {name} timed out after {timeout} seconds".format(name=self.name, timeout=self.timeout), file=sys.stderr)
        # FIXME: Job will return SIGKILL now, fail_exitcode should ignore that signal now?

    def store_job_output(self, stdout_data):
        if "stdout_destination" not in self.config:
            return

        destination = self.config["stdout_destination"]
        out = open(destination, "a")

        header = (
            "===========\n"
            "{name} ({pid}), started at {time}\n"
            "-----------\n"
        ).format(name=self.name, pid=self.process.pid, time=self.start_time)
        print(header, file=out)

        out.write(stdout_data.decode("utf-8"))

    def validate_config(self):
        assert "name" in self.config
        assert "command" in self.config
        if "schedule" in self.config:
            # No tricky assignments.
            assert "=" not in self.config["schedule"]
            # Legal cron, but I don't want to deal with it.
            assert "@" not in self.config["schedule"]

            # Be sure the schedule is valid.
            terms = self.config["schedule"].split()
            assert len(terms) == 5
