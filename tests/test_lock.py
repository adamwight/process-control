import os.path

from processcontrol import config
from processcontrol import lock


def setup_module():
    config.setup_logging()


def tearDown():
    # Clean up any old lockfiles.
    if lock.lockfile is not None:
        if os.path.exists(lock.lockfile):
            os.unlink(lock.lockfile)


def test_success():
    tag = "success"
    lock.begin(slug=tag)
    assert lock.lockfile
    path = lock.lockfile
    assert os.path.exists(lock.lockfile)

    lock.end()
    assert not os.path.exists(path)


def test_live_lock():
    raised = False
    tag = "live"
    lock.begin(slug=tag)

    try:
        # Will die because the process (this one) is still running.
        lock.begin(slug=tag)
    except lock.LockError as e:
        assert e.code == lock.LockError.LOCK_EXISTS
        raised = True

    assert raised


def test_stale_lock():
    tag = "stale"
    lock.begin(slug=tag)

    # Make the lockfile stale by changing the process ID.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("-1")
    f.close()

    lock.begin(slug=tag)

    # Check that we overwrote the contents with the current PID.
    assert lock.lockfile
    f = open(lock.lockfile, "r")
    pid = int(f.read())
    f.close()
    assert pid == os.getpid()

    lock.end()


def test_stale_lock_failopen():
    raised = False
    tag = "stale-open"
    lock.begin(slug=tag)

    # Make the lockfile stale by changing the process ID.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("-1")
    f.close()

    try:
        lock.begin(slug=tag, failopen=True)
    except lock.LockError as e:
        assert e.code == lock.LockError.STALE_LOCKFILE
        raised = True

    assert raised


def test_invalid_lock():
    tag = "stale"
    lock.begin(slug=tag)

    # Make the lockfile invalid by changing the process ID to non-numeric.
    assert lock.lockfile
    f = open(lock.lockfile, "w")
    f.write("ABC")
    f.close()

    lock.begin(slug=tag)

    # Check that we overwrote the contents with the current PID.
    assert lock.lockfile
    f = open(lock.lockfile, "r")
    pid = int(f.read())
    f.close()
    assert pid == os.getpid()

    lock.end()


def test_double_unlock():
    tag = "unlock-unlock"
    lock.begin(slug=tag)
    lock.end()

    # Should silently have nothing to do.
    lock.end()
