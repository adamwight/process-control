Job wrapper which does a bit of bookkeeping for a subprocess.

* Prevents simultaneous runners by saving a lock file per job.
* Configurable by commandline or config file parameters.
* Captures stdout and stderr, and can do TBD things with the output.
* Can prevent future job runs when unrecoverable failure conditions are detected.

To run a job, point at its description file:
    crash-override job-desc.yaml

A job description file has the following format,

```yaml
name: Take This Job and Shove It

command: /usr/local/bin/timecard --start 9:00 --end 5:30

# Optional timeout in seconds, after which your job will be aborted.  Defaults to 10 minutes, JobWrapper.DEFAULT_TIMEOUT
timeout: 30

# Optional filename for the job output.  All output will be concatenated into this file, with a header for each job.
stdout_destination: "/tmp/jobnuts.log"
```

TODO:
* Syslog actions, at least when tweezing new crontabs.
* Log invocations.
