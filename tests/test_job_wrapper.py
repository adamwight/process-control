import datetime
import iocapture
import nose
import os

import job_wrapper


data_dir = os.path.dirname(__file__) + "/data"


def run_job(filename):
    path = data_dir + "/" + filename
    job = job_wrapper.JobWrapper(config_path=path)

    job.run()


def test_success():
    with iocapture.capture() as captured:
        run_job("successful.yaml")

        assert captured.stdout == ""
        assert captured.stderr == ""


def test_return_code():
    with iocapture.capture() as captured:
        run_job("return_code.yaml")

        assert captured.stdout == ""
        assert captured.stderr == "Job False job failed with code 1\n"


# Must finish in less than two seconds, i.e. must have timed out.
@nose.tools.timed(2)
def test_timeout():
    with iocapture.capture() as captured:
        run_job("timeout.yaml")

        assert captured.stdout == ""
        assert captured.stderr == (
            "Job Timing out job timed out after 0.1 seconds\n"
            "Job Timing out job failed with code -9\n"
        )


def test_stderr():
    with iocapture.capture() as captured:
        run_job("errors.yaml")

        assert captured.stdout == ""
        assert captured.stderr == (
            "Job Bad grep job printed things to stderr:\n"
            "grep: Invalid regular expression\n\n"
            "Job Bad grep job failed with code 2\n"
        )
