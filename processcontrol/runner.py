import datetime
import os
import pwd
import shlex
import subprocess
import threading

from . import config
from . import lock
from . import mailer
from . import output_streamer


class JobRunner(object):
    def __init__(self, job):
        self.global_config = config.GlobalConfiguration()
        self.job = job
        self.mailer = mailer.Mailer(self.job)
        self.logfile = None

    def run(self):
        # Check that we are the service user.
        service_user = str(self.global_config.get("user"))
        if service_user.isdigit():
            passwd_entry = pwd.getpwuid(int(service_user))
        else:
            passwd_entry = pwd.getpwnam(service_user)
        assert passwd_entry.pw_uid == os.getuid()

        lock.begin(job_tag=self.job.slug)
        self.start_time = datetime.datetime.utcnow()

        config.log.info("Running job {name} ({slug})".format(name=self.job.name, slug=self.job.slug))

        # Spawn timeout monitor thread.
        if self.job.timeout > 0:
            # Convert minutes to seconds.
            timeout_seconds = self.job.timeout * 60
            timer = threading.Timer(timeout_seconds, self.fail_timeout)
            timer.start()

        try:
            for command_line in self.job.commands:
                self.run_command(command_line)
        finally:
            lock.end()
            if self.job.timeout > 0:
                timer.cancel()

    def run_command(self, command_string):
        # TODO: Log commandline into the output log as well.
        config.log.info("Running command: {cmd}".format(cmd=command_string))

        command = shlex.split(command_string)

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.job.environment)
        streamer = output_streamer.OutputStreamer(self.process, self.job.slug, self.start_time)
        self.logfile = streamer.filename
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
        message = "{name} failed with code {code}".format(name=self.job.name, code=return_code)
        config.log.error(message)
        # TODO: Prevent future jobs according to config.
        self.mailer.fail_mail(message, logfile=self.logfile)
        raise JobFailure(message)

    def fail_has_stderr(self, stderr_data):
        message = "{name} printed things to stderr:".format(name=self.job.name)
        config.log.error(message)
        body = stderr_data.decode("utf-8")
        config.log.error(body)
        self.mailer.fail_mail(message, body, logfile=self.logfile)
        raise JobFailure(message)

    def fail_timeout(self):
        self.process.kill()
        message = "{name} timed out after {timeout} minutes".format(name=self.job.name, timeout=self.job.timeout)
        config.log.error(message)
        self.mailer.fail_mail(message, logfile=self.logfile)
        # FIXME: Job will return SIGKILL now, fail_exitcode should ignore that signal now?
        raise JobFailure(message)

    def status(self):
        """Check for any running instances of this job, in this process or another.

        Returns a crappy dict, or None if no process is found.

        Do not use this function to gate the workflow, explicitly assert the
        lock instead."""

        # FIXME: DRY--find a good line to cut at to split out lock.read_pid.
        lock_path = lock.path_for_job(self.job.slug)
        if os.path.exists(lock_path):
            with open(lock_path, "r") as f:
                pid = int(f.read().strip())
                # TODO: encapsulate
                return {"status": "running", "pid": pid}

        return None


class JobFailure(RuntimeError):
    pass
