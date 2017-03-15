Job wrapper which does a bit of bookkeeping for a subprocess.

* Prevents simultaneous runners by saving a lock file per job.
* Configurable by commandline or config file parameters.
* Captures stdout and stderr, and can do TBD things with the output.
* Can prevent future job runs when unrecoverable failure conditions are detected.
