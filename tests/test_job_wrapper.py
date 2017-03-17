from mock import patch
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


@patch("smtplib.SMTP")
def test_return_code(MockSmtp):
    expected = "Job False job failed with code 1\n"
    with iocapture.capture() as captured:
        run_job("return_code.yaml")

        assert captured.stdout == ""
        assert captured.stderr == expected

    MockSmtp().sendmail.assert_called_once()


# Must finish in less than two seconds, i.e. must have timed out.
@nose.tools.timed(2)
@patch("smtplib.SMTP")
def test_timeout(MockSmtp):
    with iocapture.capture() as captured:
        run_job("timeout.yaml")

        assert captured.stdout == ""
        assert captured.stderr == (
            "Job Timing out job timed out after 0.1 seconds\n"
            "Job Timing out job failed with code -9\n"
        )

    MockSmtp().sendmail.assert_called_once()


@patch("smtplib.SMTP")
def test_stderr(MockSmtp):
    with iocapture.capture() as captured:
        run_job("errors.yaml")

        assert captured.stdout == ""
        assert captured.stderr == (
            "Job Bad grep job printed things to stderr:\n"
            "grep: Invalid regular expression\n\n"
            "Job Bad grep job failed with code 2\n"
        )

    MockSmtp().sendmail.assert_called_once()


def test_store_output():
    path = "/tmp/which_out.log"

    if os.path.exists(path):
        os.unlink(path)

    run_job("which_out.yaml")

    contents = open(path, "r").read()
    lines = contents.split("\n")

    assert len(lines) == 6
    assert lines[4] == "/bin/bash"

    os.unlink(path)
