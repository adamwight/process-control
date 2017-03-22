Job wrapper which does a bit of bookkeeping for a subprocess.

* Prevents simultaneous runners by saving a lock file per job.
* Configurable by config file parameters.
* Captures stdout and stderr.  We can redirect stdout to a
file.  Any stderr is interpreted as a job failure.

Configuration
=======

Global configuration must be created before you can run jobs (FIXME: works out
of the box).  Copy the file /usr/share/doc/process-control/process-control.example.yaml
to /etc/fundraising/process-control.yaml

Job descriptions
=======

A job description file has the following format,

```yaml
name: Take This Job and Shove It

# The commandline that will be run.  This is executed from Python and not from
# a shell, so globbing and other trickery will not work.  Please give a full
# path to the executable.
command: /usr/local/bin/timecard --start 9:00 --end 5:30

# Optional schedule, in Vixie cron format:
# minute hour day-of-month month day-of-week
schedule: "*/5 * * * *"

# Optional flag to prevent scheduled job execution.  The job
# can still be run as a single-shot.
disabled: true

# Optional timeout in seconds, after which your job will be
# aborted.  Defaults to 10 minutes, JobWrapper.DEFAULT_TIMEOUT
timeout: 30
```

Running
=======
To run a job, point at its description file:
    run-job job-desc.yaml

Failure detection
======

The following conditions will be interpreted as a job failure, after
which we report the problem to stderr and exit with a non-zero return
code.

* Any output on stderr.  This output is relayed back to the calling
process stderr, so may be included in failure email at the moment.
* Non-zero subprocess exit code.
* Timeout.


TODO
====

* Syslog actions, at least when tweezing new crontabs.
* Log invocations.
* Prevent future job runs when unrecoverable failure conditions are detected.
* Should we support commandline flags?
* Fine-tuning of failure detection.
* Script to kill jobs.
* Script to run a job one-off.
* Job group tags.
* Slow-start and monitoring.
* Optional backoff.
