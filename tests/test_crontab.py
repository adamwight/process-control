import os.path

from processcontrol import crontab
from processcontrol import config


def setup_module():
    from processcontrol import config
    data_dir = os.path.dirname(__file__) + "/data"
    config.GlobalConfiguration.global_config_path = data_dir + "/global_defaults.yaml"


def test_crontab():
    test_conf_dir = os.path.dirname(__file__) + "/data/scheduled"
    tab = crontab.make_cron(test_conf_dir)

    # Strip regional variations.
    tab = tab.replace(test_conf_dir, "X")
    configuration = config.GlobalConfiguration()
    tab = tab.replace(configuration.get('runner_path'), "Y")

    expected = """# Skipping disabled job X/disabled.yaml
# Generated from X/schedule_2.yaml
*/10 * * * * jenkins Y X/schedule_2.yaml
# Generated from X/schedule_good.yaml
*/5 * * * * jenkins Y X/schedule_good.yaml
# Skipping disabled job X/unscheduled.yaml
"""

    assert expected == tab
