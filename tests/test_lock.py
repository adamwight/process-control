import nose
import os.path

import lock


def tearDown():
    # Clean up any old lockfiles.
    if lock.lockfile != None:
        if os.path.exists(lock.lockfile):
            os.unlink(lock.lockfile)


def test_success():
    tag = "success"
    lock.begin(job_tag=tag)
    assert lock.lockfile
    assert os.path.exists(lock.lockfile)

    lock.end()
    assert not os.path.exists(lock.lockfile)


@nose.tools.raises(lock.LockError)
def test_live_lock():
    tag = "live"
    lock.begin(job_tag=tag)

    # Will die because the process (this one) is still running.
    lock.begin(job_tag=tag)


def test_stale_lock():
    tag = "stale"
    lock.begin(job_tag=tag)

    # Make the lockfile stale by changing the process ID.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("-1")
    f.close()

    lock.begin(job_tag=tag)

    # Check that we overwrote the contents with the current PID.
    assert lock.lockfile
    f = open(lock.lockfile, "r")
    pid = int(f.read())
    f.close()
    assert pid == os.getpid()

    lock.end()


@nose.tools.raises(lock.LockError)
def test_stale_lock_failopen():
    tag = "stale-open"
    lock.begin(job_tag=tag, failopen=True)

    # Make the lockfile stale by changing the process ID.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("-1")
    f.close()

    lock.begin(job_tag=tag)


def test_invalid_lock():
    tag = "stale"
    lock.begin(job_tag=tag)

    # Make the lockfile invalid by changing the process ID to non-numeric.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("ABC")
    f.close()

    lock.begin(job_tag=tag)

    # Check that we overwrote the contents with the current PID.
    assert lock.lockfile
    f = open(lock.lockfile, "r")
    pid = int(f.read())
    f.close()
    assert pid == os.getpid()

    lock.end()


@nose.tools.raises(lock.LockError)
def test_double_unlock():
    tag = "unlock-unlock"
    lock.begin(job_tag=tag)
    lock.end()

    # Should throw an exception.
    lock.end()
