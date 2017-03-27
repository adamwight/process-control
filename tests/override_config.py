import mock
import os
import yaml

from processcontrol import config


data_dir = os.path.dirname(__file__) + "/data"
DEFAULT_TEST_CONFIG = data_dir + "/global_defaults.yaml"

patcher = None


def start(config_path=DEFAULT_TEST_CONFIG, job_subdir=None, extra={}):
    """Start mocking GlobalConfiguration"""

    OverrideConfiguration.config_path = config_path

    if job_subdir is not None:
        extra["job_directory"] = data_dir + "/" + job_subdir

    OverrideConfiguration.extra = extra

    global patcher
    patcher = mock.patch('processcontrol.config.GlobalConfiguration', wraps=OverrideConfiguration)
    patcher.start()


def stop():
    patcher.stop()


class OverrideConfiguration(config.GlobalConfiguration):
    config_path = None
    extra = None

    def __init__(self):
        config.Configuration.__init__(self)

        test_config = yaml.safe_load(open(self.config_path, "r"))
        self.values.update(test_config)
        self.values.update(self.extra)
