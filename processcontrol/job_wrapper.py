from __future__ import print_function
import datetime
import glob
import os
import shlex
import subprocess
import sys
import threading

from . import config
from . import lock
from . import mailer


def load(job_name):
    job_directory = config.GlobalConfiguration().get("job_directory")
    job_path = "{job_dir}/{job_name}.yaml".format(job_dir=job_directory, job_name=job_name)
    return JobWrapper(config_path=job_path, slug=job_name)


def list():
    """Return a tuple of all available job names."""
    job_directory = config.GlobalConfiguration().get("job_directory")
    paths = sorted(glob.glob(job_directory + "/*.yaml"))
    file_names = [os.path.basename(p) for p in paths]
    job_names = [f.replace(".yaml", "") for f in file_names]
    return job_names


class JobWrapper(object):
    def __init__(self, config_path=None, slug=None):
        self.global_config = config.GlobalConfiguration()
        self.config_path = config_path
        self.config = config.JobConfiguration(self.global_config, self.config_path)

        self.name = self.config.get("name")
        self.slug = slug
        self.start_time = datetime.datetime.utcnow()
        self.mailer = mailer.Mailer(self.config)
        self.timeout = self.config.get("timeout")

        if self.config.has("disabled") and self.config.get("disabled") is True:
            self.enabled = False
        else:
            self.enabled = True

        if not self.config.has("schedule"):
            self.enabled = False

        if self.config.has("environment"):
            self.environment = self.config.get("environment")
        else:
            self.environment = {}

    def run(self):
        lock.begin(job_tag=self.name)

        command = shlex.split(self.config.get("command"))

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.environment)
        timer = threading.Timer(self.timeout, self.fail_timeout)
        timer.start()

        try:
            # FIXME: This doesn't stream, so large output will be buffered in memory.
            (stdout_data, stderr_data) = self.process.communicate()

            self.store_job_output(stdout_data, stderr_data)

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

    def store_job_output(self, stdout_data, stderr_data):
        output_directory = self.global_config.get("output_directory")
        assert os.access(output_directory, os.W_OK)

        job_directory = output_directory + "/" + self.name
        if not os.path.exists(job_directory):
            os.makedirs(job_directory)

        timestamp = self.start_time.strftime("%Y%m%d-%H%M%S")
        filename = "{logdir}/{name}-{timestamp}.log".format(logdir=job_directory, name=self.name, timestamp=timestamp)
        with open(filename, "a") as out:
            header = (
                "===========\n"
                "{name} ({pid}), started at {time}\n"
                "-----------\n"
            ).format(name=self.name, pid=self.process.pid, time=self.start_time.isoformat())
            print(header, file=out)

            if len(stdout_data) == 0:
                buf = "* No output *\n"
            else:
                buf = stdout_data.decode("utf-8")
            out.write(buf)

            if len(stderr_data) > 0:
                header = (
                    "-----------\n",
                    "Even worse, the job emitted errors:\n",
                    "-----------\n",
                )
                print(header, file=out)

                out.write(stderr_data.decode("utf-8"))
