import logging
import logging.config
import os
import sys
import threading

from . import config


def make_logfile_path(slug, start_time):
    """
    Makes the output file path and creates parent directory if needed
    """
    output_directory = config.GlobalConfiguration().get("output_directory")
    assert os.access(output_directory, os.W_OK), "Make sure directory '{path}' exists and is writable".format(path=output_directory)

    # per-job directory
    job_log_directory = output_directory + "/" + slug
    if not os.path.exists(job_log_directory):
        os.makedirs(job_log_directory)

    timestamp = start_time.strftime("%Y%m%d-%H%M%S")
    return "{logdir}/{name}-{timestamp}.log".format(logdir=job_log_directory, name=slug, timestamp=timestamp)


class OutputStreamer(object):

    def __init__(self, process, slug, cmdline, start_time):
        self.out_stream = process.stdout
        self.err_stream = process.stderr
        self.pid = process.pid
        self.slug = slug
        self.cmdline = cmdline
        self.filename = make_logfile_path(slug, start_time)
        self.logger = None
        self.threads = {}
        self.log_handlers = []

    def start(self):
        self.init_logger()

        self.log_header()

        self.start_reading(self.out_stream, "stdout")
        self.start_reading(self.err_stream, "stderr", is_error_stream=True)

    def log_header(self):
        # TODO: maybe expose the header as a configurable template.
        self.logger.info("===========")
        self.logger.info("{cmdline} ({pid})".format(cmdline=self.cmdline, pid=self.pid))
        self.logger.info("-----------")

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

    def init_logger(self):
        if self.logger is not None:
            return

        self.logger = logging.getLogger(self.slug)
        self.logger.setLevel(logging.INFO)

        log_file_handler = logging.FileHandler(self.filename)
        formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
        log_file_handler.setFormatter(formatter)

        self.log_handlers.append(log_file_handler)
        self.logger.addHandler(log_file_handler)

        if sys.stdout.isatty():
            # Mirror to the console if run interactively.
            console_handler = logging.StreamHandler(sys.stdout)
            self.log_handlers.append(console_handler)
            self.logger.addHandler(console_handler)

    def stop(self):
        for thread in self.threads.values():
            thread.join()
        self.logger.info("----------- end command output")

        # FIXME: sorry, I don't know what else to do.  If we keep adding file
        # handlers, we're in hot soup.
        for handler in self.log_handlers:
            self.logger.removeHandler(handler)
        self.log_handlers = []
