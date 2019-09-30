from socketserver import UnixStreamServer, StreamRequestHandler
from logging import getLogger, basicConfig, WARNING
from sys import stdout, stdin, argv
from select import select
from os import unlink
from typing import Iterable
from argparse import ArgumentParser
from atexit import register as atext_register

import logging

LOG_FILE = __file__ + '.log'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_LEVEL = WARNING

basicConfig(filename=LOG_FILE, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = getLogger("python-server")


def send_to_skill(data: str) -> None:
    stdout.write(data)
    stdout.write("\n")
    stdout.flush()


def read_from_skill() -> str:
    readable, _, _ = select([stdin], [], [], 5)

    if readable:
        return stdin.readline()

    return 'failure <timeout>'


class UnixServer(UnixStreamServer):
    request_queue_size = 0


class Handler(StreamRequestHandler):
    def receive_all(self, remaining: int) -> Iterable[bytes]:
        while remaining:
            data = self.request.recv(remaining)
            remaining -= len(data)
            yield data

    def handle_one_request(self) -> bool:
        length = self.request.recv(10)
        if not length:
            logger.warning("client {} lost connection".format(self.client_address))
            return False
        logger.info("got length {}".format(length))

        length = int(length)
        command = b''.join(self.receive_all(length))

        logger.info("received {} bytes".format(len(command)))

        if command.startswith(b'close'):
            logger.info("client {} disconnected".format(self.client_address))
            return False
        logger.info("got data {}".format(command[:1000]))

        send_to_skill(command.decode())
        logger.info("sent data to skill")
        result = read_from_skill().encode()
        logger.info("got response form skill {!r}".format(result[:1000]))

        self.request.send('{:10}'.format(len(result)).encode())
        self.request.send(result)
        logger.info("sent response to client")

        return True

    def try_handle_one_request(self) -> bool:
        try:
            return self.handle_one_request()
        except Exception as e:
            logger.exception(e)
            return False

    def handle(self) -> None:
        logger.info("client {} connected".format(self.client_address))
        client_is_connected = True
        while client_is_connected:
            client_is_connected = self.try_handle_one_request()
            logger.info("loop continue?")
        logger.info("loop ended")


def cleanup(socket: str) -> None:
    try:
        unlink(socket)
    except FileNotFoundError:
        pass


def main(socket: str, log_level: str, notify: bool) -> None:
    logger.setLevel(getattr(logging, log_level))

    atext_register(lambda: cleanup(socket))
    cleanup(socket)
    with UnixServer(socket, Handler) as server:  # type: ignore
        logger.info("starting server")
        if notify:
            send_to_skill('running')
        server.serve_forever()


if __name__ == '__main__':
    log_levels = "DEBUG WARNING INFO ERROR CRITICAL FATAL".split()
    argument_parser = ArgumentParser(argv[0])
    argument_parser.add_argument('socket')
    argument_parser.add_argument('log_level', choices=log_levels)
    argument_parser.add_argument('--notify', action='store_true')

    ns = argument_parser.parse_args()

    try:
        main(ns.socket, ns.log_level, ns.notify)
    except KeyboardInterrupt:
        pass
