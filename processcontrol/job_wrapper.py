import datetime
import glob
import os
import pwd
import shlex
import subprocess
import threading

from . import config
from . import lock
from . import mailer
from . import output_streamer


# TODO: uh has no raison d'etre now other than to demonstrate factoryness.
def load(job_name):
    return JobWrapper(slug=job_name)


def list():
    """Return a tuple of all available job names."""
    job_directory = config.GlobalConfiguration().get("job_directory")
    paths = sorted(glob.glob(job_directory + "/*.yaml"))
    file_names = [os.path.basename(p) for p in paths]
    job_names = [f.replace(".yaml", "") for f in file_names]
    return job_names


def job_path_for_slug(slug):
    global_config = config.GlobalConfiguration()
    job_directory = global_config.get("job_directory")
    path = "{root_dir}/{slug}.yaml".format(root_dir=job_directory, slug=slug)
    return path


class JobWrapper(object):
    def __init__(self, slug=None):
        self.global_config = config.GlobalConfiguration()
        self.config_path = job_path_for_slug(slug)
        self.config = config.JobConfiguration(self.global_config, self.config_path)

        self.name = self.config.get("name")
        self.slug = slug
        self.start_time = datetime.datetime.utcnow()
        self.mailer = mailer.Mailer(self.config)
        if self.config.has("timeout"):
            self.timeout = self.config.get("timeout")
        else:
            self.timeout = 0

        if self.config.has("disabled") and self.config.get("disabled") is True:
            self.enabled = False
        else:
            self.enabled = True

        if not self.config.has("schedule"):
            self.enabled = False

        self.environment = os.environ.copy()
        if self.config.has("environment"):
            self.environment.update(self.config.get("environment"))

    def run(self):
        # Check that we are the service user.
        service_user = str(self.global_config.get("user"))
        if service_user.isdigit():
            passwd_entry = pwd.getpwuid(int(service_user))
        else:
            passwd_entry = pwd.getpwnam(service_user)
        assert passwd_entry.pw_uid == os.getuid()

        lock.begin(job_tag=self.slug)

        config.log.info("Running job {name} ({slug})".format(name=self.name, slug=self.slug))

        # Spawn timeout monitor thread.
        if self.timeout > 0:
            timer = threading.Timer(self.timeout, self.fail_timeout)
            timer.start()

        command = self.config.get("command")

        if hasattr(command, "encode"):
            # Is stringlike, so cast to a list and handle along with the plural
            # case below.
            command = [command]

        try:
            for line in command:
                self.run_command(line)
        finally:
            lock.end()
            if self.timeout > 0:
                timer.cancel()

    def run_command(self, command_string):
        # TODO: Log commandline into the output log as well.
        config.log.info("Running command: {cmd}".format(cmd=command_string))

        command = shlex.split(command_string)

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.environment)
        streamer = output_streamer.OutputStreamer(self.process, self.slug, self.start_time)
        streamer.start()

        # should be safe from deadlocks because our OutputStreamer
        # has been consuming stderr and stdout
        self.process.wait()

        streamer.stop()

        return_code = self.process.returncode
        if return_code != 0:
            self.fail_exitcode(return_code)

        self.process = None

    def fail_exitcode(self, return_code):
        message = "Job {name} failed with code {code}".format(name=self.name, code=return_code)
        config.log.error(message)
        # TODO: Prevent future jobs according to config.
        self.mailer.fail_mail(message)
        raise JobFailure(message)

    def fail_has_stderr(self, stderr_data):
        message = "Job {name} printed things to stderr:".format(name=self.name)
        config.log.error(message)
        body = stderr_data.decode("utf-8")
        config.log.error(body)
        self.mailer.fail_mail(message, body)
        raise JobFailure(message)

    def fail_timeout(self):
        self.process.kill()
        message = "Job {name} timed out after {timeout} seconds".format(name=self.name, timeout=self.timeout)
        config.log.error(message)
        self.mailer.fail_mail(message)
        # FIXME: Job will return SIGKILL now, fail_exitcode should ignore that signal now?
        raise JobFailure(message)

    def status(self):
        """Check for any running instances of this job, in this process or another.

        Returns a crappy dict, or None if no process is found.

        Do not use this function to gate the workflow, explicitly assert the
        lock instead."""

        # FIXME: DRY--find a good line to cut at to split out lock.read_pid.
        lock_path = lock.path_for_job(self.slug)
        if os.path.exists(lock_path):
            with open(lock_path, "r") as f:
                pid = int(f.read().strip())
                # TODO: encapsulate
                return {"status": "running", "pid": pid}

        return None


class JobFailure(RuntimeError):
    pass
