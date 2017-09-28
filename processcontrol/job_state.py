import datetime
import yaml


from . import config


def load_state(slug):
    state = JobState(slug)
    state.load()
    return state


def statefile_path(slug):
    global_config = config.GlobalConfiguration()
    path = "{root}/{job}.yaml".format(
        root=global_config.get("state_directory"),
        job=slug)
    return path


class JobState(object):
    """Manage a statefile for each job, with information about recent run
    history."""

    def __init__(self, slug):
        self.slug = slug
        self.path = statefile_path(slug)
        self.history = []
        self.last_completion_status = "unknown"

    def load(self):
        try:
            with open(self.path, "r") as f:
                storage = yaml.safe_load(f)
        except IOError:
            # TODO: Might want to remove the file and stuff.
            return

        self.history = storage["history"]
        self.last_completion_status = storage["last_completion_status"]

    def write(self):
        # TODO: Ensure that we've called load() first, so we aren't overwriting
        # history.
        if len(self.history) > 20:
            self.history = self.history[-20:]

        contents = {
            "history": self.history,
        }

        contents["last_completion_status"] = self.last_completion_status

        with open(self.path, "w") as f:
            yaml.dump(contents, stream=f)

    def record_started(self, start_time):
        self.history.append({
            "status": "started",
            "time": start_time.isoformat(" "),
        })
        self.write()

    # TODO: We want job duration, etc.
    def record_success(self):
        self.history.append({
            "status": "completed",
            "time": datetime.datetime.utcnow().isoformat(" "),
        })
        self.last_completion_status = "success"
        self.write()

    def record_failure(self):
        self.history.append({
            "status": "failed",
            "time": datetime.datetime.utcnow().isoformat(" "),
        })
        self.last_completion_status = "failure"
        self.write()

    def record_skipped(self):
        self.history.append({
            "status": "skipped",
            "time": datetime.datetime.utcnow().isoformat(" "),
        })
        self.last_completion_status = "skipped"
        self.write()
