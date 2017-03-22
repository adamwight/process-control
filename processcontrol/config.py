import copy
import os
import yaml


class Configuration():

    def __init__(self, defaults={}):
        self.values = defaults

    def get(self, path):
        """Get a value from configuration.
        You can get a nested property by using a path delimited by
        forward slashes (/), for example "failmail/from-address".

        Trying to get a missing property raises a MissingKeyException.
        """
        parts = path.split("/")
        current = self.values

        for part in parts:
            if part not in current:
                raise MissingKeyException(path)
            current = current[part]
        return current

    def has(self, path):
        """Test for existance of a property.
        As with get(), use forward slashes to represent nested properties.
        """
        try:
            self.get(path)
        except MissingKeyException:
            return False
        return True


class MissingKeyException(Exception):

    def __init__(self, path):
        message = "Missing configuration key '" + path + "'"
        super(MissingKeyException, self).__init__(message)


class GlobalConfiguration(Configuration):

    def __init__(self):
        Configuration.__init__(self)
        self.load_global_config()

    def global_config_paths(self):
        return [
            # built-in defaults
            os.path.dirname(__file__) + "/../process-control.yaml",
            # machine config
            "/etc/fundraising/process-control.yaml",
        ]

    def load_global_config(self):
        """Load configuration from global config paths.
        Later entries override earlier entries.
        """
        for file_path in self.global_config_paths():
            if os.access(file_path, os.R_OK):
                config = yaml.safe_load(open(file_path, "r"))
                self.values.update(config)


class JobConfiguration(Configuration):

    def __init__(self, global_config, config_path):
        if global_config.has("default_job_config"):
            defaults = copy.deepcopy(global_config.get("default_job_config"))
        else:
            defaults = {}
        Configuration.__init__(self, defaults)
        self.values.update(yaml.safe_load(open(config_path, "r")))
        self.validate_job_config()

    def validate_job_config(self):
        assert "name" in self.values
        assert "command" in self.values
        if "schedule" in self.values:
            # No tricky assignments.
            assert "=" not in self.values["schedule"]
            # Legal cron, but I don't want to deal with it.
            assert "@" not in self.values["schedule"]

            # Be sure the schedule is valid.
            terms = self.values["schedule"].split()
            assert len(terms) == 5
