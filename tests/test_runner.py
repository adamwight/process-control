import glob
import mock
import nose
import os
import testfixtures

from processcontrol import runner
from processcontrol import job_spec

from . import override_config


def setup_module():
    override_config.start()


def teardown_module():
    override_config.stop()


def run_job(job_name, run_args={}):
    job = job_spec.load(job_name)
    job_runner = runner.JobRunner(job)
    job_runner.run(**run_args)


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
        # Strip off the timestamp and split into tuples.
        lines.append(line.split("\t", 1)[-1])

    return lines


@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_return_code(MockSmtp, caplog):
    run_job("return_code")

    loglines = caplog.actual()
    assert ("root", "ERROR", "False job failed with code 1") in loglines

    MockSmtp().sendmail.assert_called_once()


# Must finish in less than two seconds, i.e. must have timed out.
@nose.tools.timed(2)
@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_timeout(MockSmtp, caplog):
    run_job("timeout")

    loglines = caplog.actual()
    assert ("root", "ERROR", "Timing out job timed out after 0.005 minutes") in loglines

    MockSmtp().sendmail.assert_called_once()


@mock.patch("smtplib.SMTP")
@testfixtures.log_capture()
def test_stderr(MockSmtp, caplog):
    """Test that stderr is being routed to the log."""
    run_job("errors")

    loglines = list(caplog.actual())
    # FIXME: Use an included script, 'cos even posix output may change some day.
    assert ("errors", "ERROR", "grep: Invalid regular expression") in loglines
    # TODO: Should we go out of our way to log the non-zero return code as well?

    lines = get_output_lines("errors")
    assert "ERROR\tgrep: Invalid regular expression" in lines

    MockSmtp().sendmail.assert_called_once()


def test_store_output():
    run_job("which_out")

    lines = get_output_lines("which_out")

    assert "INFO\t/bin/bash" in lines


def test_slow_start():
    run_job("alt_command_job")

    lines = get_output_lines("alt_command_job")

    assert "INFO\tWorking hard..." in lines

    run_job("alt_command_job", {'slow_start': True})

    lines = get_output_lines("alt_command_job")

    assert "INFO\tor hardly working?" in lines


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
