import os.path

from processcontrol import crontab
from processcontrol import config

from . import override_config

data_dir = os.path.dirname(__file__) + "/data"

CONFIG_PATH = data_dir + "/global_defaults.yaml"
JOB_DIR = data_dir + "/scheduled"


def setup_module():
    override_config.start(config_path=CONFIG_PATH, extra={
        "job_directory": JOB_DIR,
    })


def teardown_module():
    override_config.stop()


def test_crontab():
    configuration = config.GlobalConfiguration()
    job_dir = configuration.get("job_directory")
    runner_path = configuration.get("runner_path")

    # Relies on global_defaults.yaml to set job_directory=./data/scheduled

    crontab.make_cron()

    with open(configuration.get("output_crontab"), "r") as f:
        tab = f.read()
    # Strip regional variations.
    tab = tab.replace(job_dir, "X")
    tab = tab.replace(runner_path, "Y")

    expected = """# Skipping disabled job disabled
# Generated from X/schedule_2.yaml
*/10 * * * * jenkins Y schedule_2
# Generated from X/schedule_good.yaml
*/5 * * * * jenkins Y schedule_good
# Skipping disabled job unscheduled
"""

    assert expected == tab
