import nose
import os

from processcontrol import config


data_dir = os.path.dirname(__file__) + "/data"


def load_config(filename, global_configuration=None):
    path = data_dir + "/" + filename
    if global_configuration is None:
        global_configuration = config.Configuration()

    configuration = config.JobConfiguration(
        global_configuration,
        config_path=path
    )
    return configuration


@nose.tools.raises(AssertionError)
def test_missing_fields():
    load_config("missing_fields.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_atsign():
    load_config("schedule_atsign.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_assign():
    load_config("schedule_assign.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_invalid():
    load_config("schedule_invalid.yaml")


def test_schedule_good():
    configuration = load_config("schedule_good.yaml")
    assert configuration.has("schedule")


def test_defaults():
    global_configuration = config.Configuration({
        "default_job_config": {
            "from_address": "they@live.com",
            "to_address": "roddy@pipermail.net"
        }
    })
    configuration = load_config("schedule_good.yaml", global_configuration)
    assert configuration.get("from_address") == "they@live.com"
    assert configuration.get("to_address") == "roddy@pipermail.net"
