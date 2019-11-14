from socketserver import UnixStreamServer, StreamRequestHandler, ThreadingMixIn
from logging import getLogger, basicConfig, WARNING, Logger
from sys import stdout, stdin, argv
from select import select
from os import unlink
from typing import Iterable, Optional
from argparse import ArgumentParser
from atexit import register as atext_register

import logging

LOG_FILE = __file__ + '.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_LEVEL = WARNING

basicConfig(filename=LOG_FILE, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = getLogger("python-server")


def send_to_skill(data: str) -> None:
    stdout.write(data)
    stdout.write("\n")
    stdout.flush()


def read_from_skill(timeout: Optional[float]) -> str:
    readable, _, _ = select([stdin], [], [], timeout)

    if readable:
        return stdin.readline()

    logger.debug("timeout")
    return 'failure <timeout>'


class SingleUnixServer(UnixStreamServer):
    request_queue_size = 0


class ThreadingUnixServer(ThreadingMixIn, UnixStreamServer):
    pass


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
        logger.info("got data {}".format(command[:1000].decode()))

        send_to_skill(command.decode())
        logger.info("sent data to skill")
        result = read_from_skill(self.server.skill_timeout).encode()  # type: ignore
        logger.info("got response from skill {!r}".format(result[:1000]))

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


def cleanup(socket: str, log: Optional[Logger] = None) -> None:
    if log:
        log.info(f"server {socket} was killed")
    try:
        unlink(socket)
    except FileNotFoundError:
        pass


def main(socket: str, log_level: str, notify: bool, single: bool,
         timeout: Optional[float]) -> None:
    logger.setLevel(getattr(logging, log_level))

    atext_register(lambda: cleanup(socket, logger))
    cleanup(socket)

    server_class = SingleUnixServer if single else ThreadingUnixServer

    with server_class(socket, Handler) as server:
        server.skill_timeout: Optional[float] = timeout  # type: ignore
        logger.info(f"starting server socket={socket} log={log_level} notify={notify} "
                    f"single={single} timeout={timeout}")
        if notify:
            send_to_skill('running')
        server.serve_forever()


if __name__ == '__main__':
    log_levels = "DEBUG WARNING INFO ERROR CRITICAL FATAL".split()
    argument_parser = ArgumentParser(argv[0])
    argument_parser.add_argument('socket')
    argument_parser.add_argument('log_level', choices=log_levels)
    argument_parser.add_argument('--notify', action='store_true')
    argument_parser.add_argument('--single', action='store_true')
    argument_parser.add_argument('--timeout', type=float, default=None)

    ns = argument_parser.parse_args()

    try:
        main(ns.socket, ns.log_level, ns.notify, ns.single, ns.timeout)
    except KeyboardInterrupt:
        pass
