import glob

from . import job_wrapper


def make_cron(config_dir):
    '''
    Read all files from the dir and output a crontab.
    '''
    out = ""

    config_files = sorted(glob.glob(config_dir + "/*.yaml"))

    for config_path in config_files:
        # FIXME just use the configuration classes, no need for job
        job = job_wrapper.JobWrapper(config_path=config_path)
        tab = JobCrontab(job)

        out += str(tab)

    return out


class JobCrontab(object):
    def __init__(self, job=None):
        self.job = job
        if job.config.has("schedule") and job.enabled:
            self.enabled = True
        else:
            self.enabled = False

    def __str__(self):
        if not self.enabled:
            return "# Skipping disabled job {path}\n".format(path=self.job.config_path)

        command = "{runner} {conf}".format(
            runner=self.job.global_config.get("runner_path"),
            conf=self.job.config_path)

        template = self.job.global_config.get("cron_template")

        out = template.format(
            source=self.job.config_path,
            schedule=self.job.config.get("schedule"),
            user=self.job.global_config.get("user"),
            command=command)

        return out
