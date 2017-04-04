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


def get_output_lines(slug):
    path_glob = "/tmp/{slug}/{slug}*.log".format(slug=slug)

    log_files = sorted(glob.glob(path_glob))
    path = log_files[-1]
    contents = open(path, "r").read()

    lines = []
    for line in contents.split("\n"):
        lines.append(line.split("\t", 1)[-1])

    return lines


@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_return_code(MockSmtp, caplog):
    with nose.tools.assert_raises(job_wrapper.JobFailure):
        run_job("return_code")

    loglines = caplog.actual()
    assert ("root", "ERROR", "Job False job failed with code 1") in loglines

    MockSmtp().sendmail.assert_called_once()


# Must finish in less than two seconds, i.e. must have timed out.
@nose.tools.timed(2)
@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_timeout(MockSmtp, caplog):
    with nose.tools.assert_raises(job_wrapper.JobFailure):
        run_job("timeout")

    loglines = caplog.actual()
    assert ("root", "ERROR", "Job Timing out job timed out after 0.005 minutes") in loglines
    assert ("root", "ERROR", "Job Timing out job failed with code -9") in loglines

    MockSmtp().sendmail.assert_called_once()


@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_stderr(MockSmtp, caplog):
    with nose.tools.assert_raises(job_wrapper.JobFailure):
        run_job("errors")

    loglines = list(caplog.actual())
    assert ("errors", "ERROR", "grep: Invalid regular expression") in loglines
    # TODO: Should we go out of our way to log the non-zero return code as well?

    lines = get_output_lines("errors")
    assert "ERROR\tgrep: Invalid regular expression" in lines

    MockSmtp().sendmail.assert_called_once()


def test_store_output():
    run_job("which_out")

    lines = get_output_lines("which_out")

    assert "INFO\t/bin/bash" in lines


def test_environment():
    os.environ["MYENV"] = "pre-existing"

    run_job("env")

    lines = get_output_lines("env")

    assert "INFO\tfoo1=bar" in lines
    assert "INFO\tfoo2=rebar" in lines
    assert "INFO\tfoo3=123" in lines
    assert "INFO\tfoo4=True" in lines
    assert "INFO\tMYENV=pre-existing" in lines


@nose.tools.raises(AssertionError)
def test_symlink():
    '''Prevent running any job config outside the job_directory.'''

    run_job("symlink")
