import logging.config
import os
import Queue
import threading

from . import config


class OutputStreamer(object):

    def __init__(self, process, slug, start_time):
        self.out_stream = process.stdout
        self.err_stream = process.stderr
        self.pid = process.pid
        self.slug = slug
        self.start_time = start_time
        self.queues = {}

    def start(self):
        self.init_logger()
        self.start_reading(self.out_stream, "stdout")
        self.start_reading(self.err_stream, "stderr", "ERROR: ")

    def get_output(self):
        return self.dump_queue("stdout")

    def get_errors(self):
        return self.dump_queue("stderr")

    def dump_queue(self, stream_name):
        lines = []
        queue = self.queues[stream_name]
        while not queue.empty():
            lines.append(queue.get())
        return "\n".join(lines)

    def start_reading(self, stream, stream_name, prefix=""):
        self.queues[stream_name] = Queue.Queue()
        thread = threading.Thread(
            target=self.read_lines,
            args=(stream, self.queues[stream_name], prefix)
        )
        thread.daemon = True
        thread.start()

    def read_lines(self, stream, queue, prefix):
        while True:
            line = stream.readline().decode("utf-8")
            if line == "":
                break
            line = line.rstrip("\n")
            # FIXME: formatters do formatting, log stderr at error
            self.logger.info(prefix + line)
            queue.put(line)

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
        filename = self.make_logfile_path()
        self.logger = logging.getLogger(self.slug)
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(filename)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        fh.setFormatter(formatter)

        self.logger.addHandler(fh)

        self.logger.info("===========")
        self.logger.info("{name} ({pid})".format(name=self.slug, pid=self.pid))
        self.logger.info("-----------")
