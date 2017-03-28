import glob
import mock
import nose
import os
import testfixtures

from processcontrol import job_wrapper

from . import override_config


def setup_module():
    override_config.start()


def teardown_module():
    override_config.stop()


def run_job(job_name):
    job = job_wrapper.load(job_name)
    job.run()


def test_success():
    run_job("successful")

    # TODO: assert more


@mock.patch("smtplib.SMTP")
def test_return_code(MockSmtp):
    with testfixtures.LogCapture() as caplog:
        run_job("return_code")

        loglines = caplog.actual()
        assert ("root", "ERROR", "Job False job failed with code 1") in loglines

    MockSmtp().sendmail.assert_called_once()


# Must finish in less than two seconds, i.e. must have timed out.
@nose.tools.timed(2)
@mock.patch("smtplib.SMTP")
def test_timeout(MockSmtp):
    with testfixtures.LogCapture() as caplog:
        run_job("timeout")

        loglines = caplog.actual()
        assert ("root", "ERROR", "Job Timing out job timed out after 0.1 seconds") in loglines
        assert ("root", "ERROR", "Job Timing out job failed with code -9") in loglines

    MockSmtp().sendmail.assert_called_once()


@mock.patch("smtplib.SMTP")
def test_stderr(MockSmtp):
    with testfixtures.LogCapture() as caplog:
        run_job("errors")

        loglines = list(caplog.actual())
        assert ("root", "ERROR", "Job Bad grep job printed things to stderr:") in loglines
        assert ("root", "ERROR", "grep: Invalid regular expression\n") in loglines
        assert ("root", "ERROR", "Job Bad grep job failed with code 2") in loglines

    MockSmtp().sendmail.assert_called_once()


def test_store_output():
    path_glob = "/tmp/Which job/Which job*.log"

    run_job("which_out")

    log_files = sorted(glob.glob(path_glob))
    path = log_files[-1]
    contents = open(path, "r").read()
    lines = contents.split("\n")

    assert len(lines) == 5
    assert "/bin/bash" in lines

    os.unlink(path)


def test_environment():
    path_glob = "/tmp/Env dumper/Env dumper*.log"

    run_job("env")

    log_files = sorted(glob.glob(path_glob))
    path = log_files[-1]
    contents = open(path, "r").read()
    lines = contents.split("\n")

    assert len(lines) == 6

    assert "foo1=bar" in lines
    assert "foo2=rebar" in lines

    os.unlink(path)
