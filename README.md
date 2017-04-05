Job wrapper which does a bit of bookkeeping for a subprocess.

* Prevents simultaneous runners by saving a lock file per job.
* Configurable by config file parameters.
* Captures stdout and stderr.  We can redirect stdout to a
file.  Any stderr is interpreted as a job failure.

Configuration
=======

Global configuration must be created before you can run jobs (FIXME: Make this
work out-of-the-box).  Copy the file
/usr/share/doc/process-control/process-control.example.yaml
to /etc/fundraising/process-control.yaml and customize it for your machine.

You'll need to pick a service user, and make /var/log/process-control writable
by that user.

Job descriptions
=======

Each job is described in a YAML file under the /var/lib/process-control
directory (by default).  See `job.example.yaml` for the available keys and
their meaninings.

Running
=======

Jobs can be run by name,
    run-job job-a-thon
which will look for a job configuration in `/var/lib/process-control/job-a-thon.yaml`.

Other actions on jobs can be accessed like:
    run-job --list-jobs

Scheduled Jobs
======

Any job that includes a `schedule` key and does not have `disabled: true` can
be automatically scheduled.  The schedule value is given as a five-term Vixie
crontab (man 5 crontab), but aliases like `@daily` are not allowed.

A script `cron-generate` will read all scheduled jobs and write entries to
/etc/cron.d/process-control, or the configured `output_crontab`.  For example,
a job `yak` with the schedule `30 12 * * *` will be written 

Cron-generate takes no arguments, its configuration is read from /etc.

    cron-generate

All cron jobs 

Failure detection
======

The following conditions will be interpreted as a job failure, after
which we report the problem to stderr and exit with a non-zero return
code.

* Any output on stderr.  This output is relayed back to the calling
process stderr, so may be included in failure email at the moment.
* Non-zero subprocess exit code.
* Timeout.

Security
======

This tool was written for a typical environment where software developers and
operations engineers have different permissions.  The design is supposed to
make it reasonably safe for a group of developers to make auditable changes to
job configuration without help from operations engineers, and it should not be
possible for users to escalate privileges to anything but running processes as
the service user.

It should also not be possible to run arbitrary job descriptions from a user's
home directory.  We recommend deploying the `job_directory` in a way that all
changes can be audited.

TODO
====

* Log invocations.
* Prevent future job runs when unrecoverable failure conditions are detected.
* Fine-tuning of failure detection.
* Job group tags.
* Slow-start and monitoring.
* Optional backoff.
