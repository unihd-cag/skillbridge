from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from queue import Queue, Empty
from select import select
from sys import executable
from os import fdopen
from pty import openpty

from skillbridge.server import python_server


class Virtuoso(Thread):
    def __init__(self, socket):
        super().__init__(daemon=True)
        self.daemon = True

        self.queue = Queue()
        self.questions = []
        self.should_run = True
        self.server = None
        self.running = False
        self.pin = None
        self.socket = socket

    def wait_until_ready(self):
        while not self.running:
            if not self.should_run:
                raise RuntimeError(f"could not start server:\n {self.server.stdout.read()}")

    def _create_subprocess(self):
        script = python_server.__file__
        master, slave = openpty()
        self.server = Popen(
            [executable, script, self.socket, "DEBUG", '--notify'],
            stdin=slave,
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True,
        )
        self.pin = fdopen(master, 'w')

    def _wait_for_notification(self):
        read = self.read()
        assert read == 'running', f"expected 'running', got {self.server.stdout.read()}"

    def run(self):
        try:
            self._run()
        finally:
            self.running = False
            self.should_run = False
            self.server.kill()
            self.server.wait()

    def _run(self):
        self._create_subprocess()
        self._wait_for_notification()

        while self.should_run:
            self.running = True

            question = self.read()
            if question is None:
                continue
            self.questions.append(question)

            try:
                answer = self.queue.get_nowait()
            except Empty:
                raise RuntimeError(f"no answer available for {question!r}")
            self.write(answer)

    def read(self):
        # we need to wait pretty long here, because sometimes it takes really long
        # to start the server
        for timeout in (0.1, 0.5, 1, 2, 4, 8):
            if not self.should_run:
                return
            readable, _, _ = select([self.server.stdout], [], [], timeout)
            if readable:
                return self.server.stdout.readline().strip()

    def write(self, message):
        self.pin.write(message + '\n')

    def stop(self):
        self.should_run = False
        self.join()
        self.server.kill()
        self.server.wait()

    def answer_with(self, status, message):
        self.queue.put(status + ' ' + message)

    def answer_success(self, message):
        self.answer_with('success', message)

    def answer_object(self, type_, address, object_type=()):
        self.answer_success(f'Remote("__py_{type_}_{address}")')
        if object_type != ():
            self.answer_success(repr(object_type))

    def answer_failure(self, message):
        self.answer_with('failure', message)

    @property
    def last_question(self):
        if self.questions:
            return self.questions.pop()
