import os
import os.path

from processcontrol import crontab
from processcontrol import config

from . import override_config


data_dir = os.path.dirname(__file__) + "/data"

JOB_DIR = data_dir + "/scheduled"


def setup_module():
    override_config.start(extra={
        "job_directory": JOB_DIR,
    })


def teardown_module():
    override_config.stop()


def test_crontab():
    configuration = config.GlobalConfiguration()
    job_dir = configuration.get("job_directory")
    runner_path = configuration.get("runner_path")

    crontab.make_cron()

    with open(configuration.get("output_crontab"), "r") as f:
        tab = f.read()
    # Strip regional variations.
    tab = tab.replace(job_dir, "X")
    tab = tab.replace(runner_path, "Y")
    tab = tab.replace(str(os.getuid()), "Z")

    expected = """# Skipping disabled job disabled
# Generated from X/schedule_2.yaml
*/10 * * * * Z Y --job schedule_2
# Generated from X/schedule_good.yaml
*/5 * * * * Z Y --job schedule_good
# Skipping disabled job unscheduled
"""

    assert expected == tab
