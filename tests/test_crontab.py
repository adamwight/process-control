import os.path

import crontab


def test_crontab():
    test_conf_dir = os.path.dirname(__file__) + "/data/scheduled"
    tab = crontab.make_cron(test_conf_dir)

    # Strip regional variations.
    tab = tab.replace(test_conf_dir, "X")
    tab = tab.replace(crontab.RUNNER_PATH, "Y")

    expected = """# Generated from X/schedule_2.yaml
*/10 * * * * jenkins Y X/schedule_2.yaml
# Generated from X/schedule_good.yaml
*/5 * * * * jenkins Y X/schedule_good.yaml
# Skipping disabled job X/unscheduled.yaml
"""

    assert expected == tab
