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

        self.killer_was_me = False
        self.failure_reason = None

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
                return_code = self.run_command(command_line)
                if return_code != 0:
                    self.fail_exitcode(return_code)
        except JobFailure as ex:
            config.log.error(ex.message)
            self.mailer.fail_mail(ex.message, logfile=self.logfile)
            raise
        finally:
            if self.job.timeout > 0:
                # This becomes relevant when running multiple commands.
                timer.cancel()
            lock.end()

    def run_command(self, command_string):
        """Fork a command, record its outputs to a logfile and return the
        integer exit code."""
        # TODO: Log commandline into the output log as well.
        config.log.info("Running command: {cmd}".format(cmd=command_string))

        command = shlex.split(command_string)

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.job.environment)
        streamer = output_streamer.OutputStreamer(self.process, self.job.slug, command_string, self.start_time)
        self.logfile = streamer.filename
        streamer.start()

        # should be safe from deadlocks because our OutputStreamer
        # has been consuming stderr and stdout
        self.process.wait()

        streamer.stop()

        return_code = self.process.returncode

        self.process = None

        return return_code

    def fail_exitcode(self, return_code):
        # Check if this is an expected non-zero return code, i.e. we sent the
        # process a kill signal.
        if self.killer_was_me:
            # We already know, so pass through the failure reason.
            message = self.failure_reason
        else:
            message = "{name} failed with code {code}".format(name=self.job.name, code=return_code)
        # TODO: Prevent future jobs according to config.
        raise JobFailure(message)

    def fail_timeout(self):
        # Send a message to self using cheap IPC.
        # FIXME: or is this not safe?
        self.killer_was_me = True
        self.failure_reason = "{name} timed out after {timeout} minutes".format(
            name=self.job.name, timeout=self.job.timeout)

        config.log.warning("Killing subprocess due to timeout")
        self.process.kill()
        # Note that we're on a separate thread, so instead of raising an
        # exception, we rely on process.kill() to trigger fail_exitcode(-9) in
        # the parent thread.

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
