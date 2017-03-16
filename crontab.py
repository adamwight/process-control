import glob
import os.path

import job_wrapper


# FIXME: global config
DEFAULT_USER = "jenkins"

CRON_TEMPLATE = """# Generated from {source}
{schedule} {user} {command}
"""

RUNNER_PATH = os.path.dirname(__file__) + "/crash-override"


def make_cron(config_dir):
    '''
    Read all files from the dir and output a crontab.
    '''
    out = ""

    config_files = sorted(glob.glob(config_dir + "/*.yaml"))

    for config_path in config_files:
        job = job_wrapper.JobWrapper(config_path=config_path)
        tab = JobCrontab(job)

        out += str(tab)

    return out


class JobCrontab(object):
    def __init__(self, job=None):
        self.job = job
        if "schedule" in job.config and job.enabled:
            self.enabled = True
        else:
            self.enabled = False

    def __str__(self):
        if not self.enabled:
            return "# Skipping disabled job {path}\n".format(path=self.job.config_path)

        command = "{runner} {conf}".format(
            runner=RUNNER_PATH,
            conf=self.job.config_path)

        out = CRON_TEMPLATE.format(
            source=self.job.config_path,
            schedule=self.job.config["schedule"],
            user=DEFAULT_USER,
            command=command)

        return out