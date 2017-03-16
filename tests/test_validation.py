import nose
import os

import job_wrapper


data_dir = os.path.dirname(__file__) + "/data"


def load_job(filename):
    path = data_dir + "/" + filename
    job = job_wrapper.JobWrapper(config_path=path)
    return job


@nose.tools.raises(AssertionError)
def test_missing_fields():
    load_job("missing_fields.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_atsign():
    load_job("schedule_atsign.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_assign():
    load_job("schedule_assign.yaml")


@nose.tools.raises(AssertionError)
def test_schedule_invalid():
    load_job("schedule_invalid.yaml")


def test_schedule_good():
    job = load_job("schedule_good.yaml")
    assert job.config["schedule"]
