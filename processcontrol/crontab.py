from __future__ import print_function

from . import config
from . import job_wrapper


def make_cron():
    '''
    Read all files from the dir and output a crontab.
    '''

    jobs = job_wrapper.list()
    cron_text = ""

    for job_name in jobs:
        # FIXME just use the configuration classes, no need for job
        job = job_wrapper.load(job_name)
        tab = JobCrontab(job)

        cron_text += str(tab)

    global_config = config.GlobalConfiguration()
    output_file = global_config.get("output_crontab")
    if output_file == 'console':
        print(cron_text)
    else:
        with open(output_file, "w") as out:
            out.write(cron_text)


class JobCrontab(object):
    def __init__(self, job=None):
        self.job = job
        if job.config.has("schedule") and job.enabled:
            self.enabled = True
        else:
            self.enabled = False

    def __str__(self):
        if not self.enabled:
            return "# Skipping disabled job {name}\n".format(name=self.job.slug)

        command = "{runner} {name}".format(
            runner=self.job.global_config.get("runner_path"),
            name=self.job.slug)

        template = self.job.global_config.get("cron_template")

        out = template.format(
            source=self.job.config_path,
            schedule=self.job.config.get("schedule"),
            user=self.job.global_config.get("user"),
            command=command)

        return out
