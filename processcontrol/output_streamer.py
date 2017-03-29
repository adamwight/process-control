import logging.config
import os
import threading

from . import config


class OutputStreamer(object):

    def __init__(self, process, slug, start_time):
        self.out_stream = process.stdout
        self.err_stream = process.stderr
        self.pid = process.pid
        self.slug = slug
        self.start_time = start_time
        self.filename = self.make_logfile_path()
        self.logger = None
        self.threads = {}

    def start(self):
        self.init_logger()
        self.start_reading(self.out_stream, "stdout")
        self.start_reading(self.err_stream, "stderr", is_error_stream=True)

    def start_reading(self, stream, stream_name, is_error_stream=False):
        thread = threading.Thread(
            target=self.read_lines,
            args=(stream, ),
            kwargs={"is_error_stream": is_error_stream}
        )
        thread.daemon = True
        thread.start()
        self.threads[stream_name] = thread

    def read_lines(self, stream, is_error_stream=False):
        while True:
            line = stream.readline().decode("utf-8")
            if line == "":
                break
            line = line.rstrip("\n")
            # FIXME: formatters do formatting
            if is_error_stream:
                self.logger.error(line)
            else:
                self.logger.info(line)

    def make_logfile_path(self):
        """
        Makes the output file path and creates parent directory if needed
        """
        output_directory = config.GlobalConfiguration().get("output_directory")
        assert os.access(output_directory, os.W_OK)

        # per-job directory
        job_directory = output_directory + "/" + self.slug
        if not os.path.exists(job_directory):
            os.makedirs(job_directory)

        timestamp = self.start_time.strftime("%Y%m%d-%H%M%S")
        return "{logdir}/{name}-{timestamp}.log".format(logdir=job_directory, name=self.slug, timestamp=timestamp)

    def init_logger(self):
        if self.logger is not None:
            return

        self.logger = logging.getLogger(self.slug)
        self.logger.setLevel(logging.INFO)

        self.log_file_handler = logging.FileHandler(self.filename)
        formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
        self.log_file_handler.setFormatter(formatter)

        self.logger.addHandler(self.log_file_handler)

        # FIXME: gets written for each subprocess, so the name=slug is not
        # quite right.  Should be the commandline?
        self.logger.info("===========")
        self.logger.info("{name} ({pid})".format(name=self.slug, pid=self.pid))
        self.logger.info("-----------")

    def stop(self):
        for thread in self.threads.values():
            thread.join()
        self.logger.info("----------- end command output")

        # FIXME: sorry, I don't know what else to do.  If we keep adding file
        # handlers, we're in hot soup.
        self.logger.removeHandler(self.log_file_handler)
