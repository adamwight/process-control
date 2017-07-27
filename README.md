Job wrapper which does a bit of bookkeeping.

* Schedule jobs using cron syntax, while isolating users from cron write
access.
* Configuration is done entirely through YAML files, for auditability and
declarativeness.
* Enforce running jobs as a service user.
* Prevents overlapping runners by saving a lock file per job.
* Timeout
* Captures stdout and stderr, and log to a file per run.

Configuration
=======

Global configuration must be created before you can run jobs (FIXME: Make this
work out-of-the-box).  Copy the file
/usr/share/doc/process-control/process-control.example.yaml
to /etc/process-control.yaml and customize it for your machine.

You'll need to pick a service user, and create the `job_directory` and
`output_directory` specified in your configuration.  These directories must be
writable by the service user.

Job descriptions
=======

Each job is described in a YAML file under the /var/lib/process-control
directory (by default).  See `job.example.yaml` for the available keys and
their meaninings.

Note that defaults will be taken from the global `default_job_config` section.

Running
=======

Jobs can be run by name,

    run-job --job cpu_marathon

which will look for a job configuration in `/var/lib/process-control/cpu_marathon.yaml`.

Other actions on jobs can be accessed like:

    run-job --list-jobs
    run-job --status

Jobs are listed in a format like so:

```
multi - Multi job
    tags: database, queue
blast - Blastoff job    {pid: 5647, status: running}
```

If a job configuration has a 'slow_start_command' defined, that alternate
 command can be run with:

    run-job --slow-start huge_job

Scheduled Jobs
======

Any job that includes a `schedule` key and does not have `disabled: true` can
be automatically scheduled.  The schedule value is given as a five-term Vixie
crontab (man 5 crontab), but aliases like `@daily` are not allowed.

A script `cron-generate` will read all scheduled jobs and write entries to
/etc/cron.d/process-control, or the configured `output_crontab`.  For example,
a job `yak` with the schedule `30 12 * * *` will be written.

Cron-generate takes no arguments, its configuration is read from /etc.

    cron-generate

The resulting crontab will look something like,

```
# Skipping disabled job ingenico_wr1_audit_parse
# Generated from /var/lib/process-control/barium/paypal_audit.yaml
35 19 * * * jenkins /usr/bin/run-job --job paypal_audit
# Generated from /var/lib/process-control/barium/paypal_smashpig_job_runner.yaml
2-59/5 * * * * jenkins /usr/bin/run-job --job paypal_smashpig_job_runner
```

All cron jobs are run as the service user.

Failure detection
======

The following conditions will be interpreted as a job failure, after which we
log the detected issues and exit with a non-zero return code.

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

* Prevent future job runs when unrecoverable failure conditions are detected.
* Fine-tuning of failure detection.
* Manipulate jobs using group tags.
* Slow-start and monitoring.
* Optional backoff.
